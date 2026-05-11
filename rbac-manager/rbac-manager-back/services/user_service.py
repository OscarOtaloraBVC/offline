# services/user_service.py
import sqlite3
from typing import List, Optional
from models.user_model import User, UserCreate, UserUpdate
from models.profile_model import Profile
from models.user_certs_model import UserCert
from database.db import get_db_connection
from datetime import datetime
from services.rbac.rbac_core import deleteOldResources
import ast

def _get_assignments_for_user(user_id: int, conn: sqlite3.Connection) -> List[dict]:
    """Helper to fetch profile-namespace assignments for a given user ID."""
    namespaces = []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id as profile_id, p.name as profile_name, p.type as profile_type, upn.namespace
        FROM users_has_profiles_namespaces upn
        JOIN profiles p ON upn.profile_id = p.id
        WHERE upn.user_id = ?
        ORDER BY upn.namespace, p.name
    """, (user_id,))
    for row in cursor.fetchall():
        row_dict = dict(row)
        namespaces.append({
            "profile": {"id": row_dict['profile_id'], "name": row_dict['profile_name'], "type": row_dict['profile_type']},
            "namespace": row_dict['namespace']
        })
    return namespaces

def create_user(user_in: UserCreate) -> Optional[User]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # updated_at will be set by DEFAULT or manually if no trigger
            # If not using DB trigger for updated_at on insert, add it here:
            # current_time = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO users (username, cert_days, observations) VALUES (?, ?, ?)",
                (user_in.username, user_in.cert_days, user_in.observations)
            )
            user_id = cursor.lastrowid
            if not user_id:
                conn.rollback()
                return None

            # Associate profiles and namespaces
            if user_in.assignments:
                for assignment in user_in.assignments:
                    profile_id = assignment.profile_id
                    namespace = assignment.namespace
                    try:
                        cursor.execute(
                            "INSERT INTO users_has_profiles_namespaces (user_id, profile_id, namespace) VALUES (?, ?, ?)",
                            (user_id, profile_id, namespace)
                        )
                    except sqlite3.IntegrityError as e: # e.g. profile_id doesn't exist
                        conn.rollback()
                        print(f"Error associating profile_id {profile_id} in namespace {namespace} to user_id {user_id}: {e}")
                        return None # Or raise specific error

            conn.commit()
            return get_user(user_id) # Fetch the complete user object
    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for username
        return None
    return None


def get_user(user_id: int) -> Optional[User]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, cert_days, observations, state,updated_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            user_data = dict(row)
            assignments = _get_assignments_for_user(user_id, conn)
            # The User model now includes 'assignments'.
            # We also synthesize the old 'profiles' and 'namespaces' fields for compatibility.
            user_data["assignments"] = assignments
            user_data["profiles"] = list({a['profile']['id']: Profile(**a['profile']) for a in assignments}.values())
            user_data["namespaces"] = [{"namespace": ns, "user_id": user_id} for ns in sorted([ns for ns in set(a['namespace'] for a in assignments) if ns is not None])]
            return User(**user_data)
    return None

def list_users() -> List[User]:
    users_list = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, cert_days, observations, state,updated_at FROM users ORDER BY username")
        user_rows = cursor.fetchall()
        for user_row_dict in [dict(row) for row in user_rows]:
            user_id = user_row_dict["id"]
            # For consistency, we'll add assignments here too, though they may not be used in the list view.
            assignments = _get_assignments_for_user(user_id, conn)
            user_row_dict["assignments"] = assignments
            # Also populate profiles and namespaces for list view if needed by frontend
            user_row_dict["profiles"] = list({a['profile']['id']: Profile(**a['profile']) for a in assignments}.values())
            user_row_dict["namespaces"] = [{"namespace": ns, "user_id": user_id} for ns in sorted([ns for ns in set(a['namespace'] for a in assignments) if ns is not None])]
            users_list.append(User(**user_row_dict))
    return users_list

def list_namespace_names(user_id: int) -> List[str]:
    namespace_name_list = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT namespace FROM users_has_profiles_namespaces WHERE user_id = ? ORDER BY namespace", (user_id,))
        namespaces_rows = cursor.fetchall()

        for row in namespaces_rows:
            namespace_name_list.append(row['namespace'])

    return namespace_name_list

def update_user(user_id: int, user_in: UserUpdate) -> Optional[User]:
    fields_to_update = []
    params = []

    if user_in.username is not None:
        fields_to_update.append("username = ?")
        params.append(user_in.username)
    if user_in.cert_days is not None:
        fields_to_update.append("cert_days = ?")
        params.append(user_in.cert_days)
    if user_in.observations is not None: # Allows setting observations to NULL if empty string passed
        fields_to_update.append("observations = ?")
        params.append(user_in.observations)
    
    # If using a DB trigger for updated_at, it will handle it automatically.
    # Otherwise, update manually:
    # fields_to_update.append("updated_at = ?")
    # params.append(datetime.utcnow().isoformat())

    if not fields_to_update and user_in.assignments is None: # Nothing to update
        if user_in.assignments is None: # And no assignments to update either
             return get_user(user_id) # No changes

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if fields_to_update:
                sql = f"UPDATE users SET {', '.join(fields_to_update)} WHERE id = ?"
                params.append(user_id)
                cursor.execute(sql, tuple(params))

            # Handle profile-namespace associations if provided
            if user_in.assignments is not None:
                # 1. Remove existing associations
                cursor.execute("DELETE FROM users_has_profiles_namespaces WHERE user_id = ?", (user_id,))
                # 2. Add new associations
                for assignment in user_in.assignments:
                    profile_id = assignment.profile_id
                    namespace = assignment.namespace
                    try:
                        cursor.execute(
                            "INSERT INTO users_has_profiles_namespaces (user_id, profile_id, namespace) VALUES (?, ?, ?)",
                            (user_id, profile_id, namespace)
                        )
                    except sqlite3.IntegrityError as e: # e.g. profile_id doesn't exist
                        conn.rollback()
                        print(f"Error associating profile_id {profile_id} in namespace {namespace} to user_id {user_id} during update: {e}")
                        return None # Or raise

            if cursor.rowcount > 0 or user_in.assignments is not None: # rowcount for user update, or if assignments were changed
                conn.commit()
                return get_user(user_id)
            else: # User not found or no actual change to user table fields
                conn.rollback() # Rollback if no actual user fields were updated
                existing_user = get_user(user_id) # Check if user exists
                if existing_user and user_in.assignments is not None: # User exists and only assignments were updated
                    return existing_user
                return None


    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for username
        return None
    return None

def delete_user(user_id: int) -> bool:
    
    #Deleting k8s objects
    uc=get_last_user_cert(user_id)
    if uc!=None:
        objs=ast.literal_eval(uc['objs_created'].replace("'","\""))
        deleteOldResources(objs,user_id)
            

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # users_has_profiles_namespaces entries will be deleted by ON DELETE CASCADE
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
        

def get_user_cert(id: int) -> Optional[UserCert]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users_certs WHERE id = ?",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row)
    return None

def get_last_user_cert(user_id: int) -> Optional[UserCert]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users_certs WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        row = cursor.fetchone()
        if row!=None:
            return dict(row)
    return None

def create_user_certs(user_cert_in: UserCert) -> Optional[UserCert]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users_certs(user_id, kubeconfig_content,objs_created) VALUES (?, ?, ?)",
                (user_cert_in.user_id, user_cert_in.kubeconfig_content, user_cert_in.objs_created)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return get_user_cert(user_id)
    except sqlite3.IntegrityError:
        return None
    return None

import ast

def disable_user(user_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Ejecutamos el UPDATE para cambiar el estado a DISABLED
            cursor.execute(
                "UPDATE users SET state = 'DISABLED' WHERE id = ?",
                (user_id,)
            )
            conn.commit()

            uc=get_last_user_cert(user_id)
            if uc!=None:
                objs=ast.literal_eval(uc['objs_created'].replace("'","\""))
                deleteOldResources(objs,user_id)
            
            # Verificamos si se modificÃ³ alguna fila (si el ID existÃ­a)
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in disable_user: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in disable_user: {e}")
        return False

def enable_user(user_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Ejecutamos el UPDATE para cambiar el estado a DISABLED
            cursor.execute(
                "UPDATE users SET state = 'ENABLED' WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            
            # Verificamos si se modificÃ³ alguna fila (si el ID existÃ­a)
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in enable_user: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in enable_user: {e}")
        return False

