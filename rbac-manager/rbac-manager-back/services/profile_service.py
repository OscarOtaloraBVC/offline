# services/profile_service.py
import sqlite3
from typing import List, Optional, Dict, Set
from models.profile_model import Profile, ProfileCreate, ProfileUpdate
from models.permission_model import Permission, PermissionCreate, PermissionUpdate
from database.db import get_db_connection

def create_profile(profile_in: ProfileCreate) -> Optional[Profile]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (name,type) VALUES (?,?)",
                (profile_in.name,profile_in.type)
            )
            conn.commit()
            profile_id = cursor.lastrowid
            if profile_id:
                return get_profile(profile_id)
    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for name
        return None # Or raise a custom exception
    return None

def get_profile(profile_id: int) -> Optional[Profile]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name,type FROM profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        if row:
            return Profile(**dict(row))
    return None

def list_profiles() -> List[Profile]:
    profiles_list = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type FROM profiles ORDER BY name")
        rows = cursor.fetchall()
        for row in rows:
            profiles_list.append(Profile(**dict(row)))
    return profiles_list

def update_profile(profile_id: int, profile_in: ProfileUpdate) -> Optional[Profile]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE profiles SET name = ? WHERE id = ?",
                (profile_in.name,profile_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return get_profile(profile_id)
    except sqlite3.IntegrityError:
        return None # Or raise
    return None

def delete_profile(profile_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # users_has_profiles entries will be deleted by ON DELETE CASCADE
        cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return cursor.rowcount > 0

def save_profile_permissions(profile_id: int, permissions_list: List[PermissionCreate]) -> bool:
    """
    Synchronizes permissions for a given profile_id.
    Deletes all existing permissions for the profile and then adds the new ones
    from permissions_list.
    Returns True on success, False on failure.
    """
    # Optional: Validate if the profile_id exists first
    # if get_profile(profile_id) is None:
    #     print(f"Error: Profile with ID {profile_id} not found.")
    #     return False

    # Input validation for duplicate resources in the incoming list
    resource_names_in_input = [p.resource for p in permissions_list]
    if len(resource_names_in_input) != len(set(resource_names_in_input)):
        # Consider logging this error more formally in a real application
        print(f"Error: Duplicate resource names found in input permissions_list for profile_id {profile_id}.")
        return False

    conn = None # Initialize for potential use in except block if `with` fails before assignment
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Delete all existing permissions for this profile_id
            # This ensures that any permissions not in the new list are removed.
            cursor.execute("DELETE FROM permissions WHERE profile_id = ?", (profile_id,))

            # Step 2: Insert new permissions if the list is not empty
            if permissions_list:
                insert_query = """
                    INSERT INTO permissions (
                        profile_id, resource, resource_api, resource_namespaced,
                        is_verb_get, is_verb_list, is_verb_watch,
                        is_verb_create, is_verb_update, is_verb_patch,
                        is_verb_delete, is_verb_deletecollection
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # Prepare data for executemany.
                # Pydantic models store booleans as True/False.
                # SQLite typically uses 0/1 for booleans.
                data_to_insert = []
                for perm_create in permissions_list:
                    data_to_insert.append((
                        profile_id,
                        perm_create.resource,
                        perm_create.resource_api,
                        int(perm_create.resource_namespaced),
                        int(perm_create.is_verb_get),
                        int(perm_create.is_verb_list),
                        int(perm_create.is_verb_watch),
                        int(perm_create.is_verb_create),
                        int(perm_create.is_verb_update),
                        int(perm_create.is_verb_patch),
                        int(perm_create.is_verb_delete),
                        int(perm_create.is_verb_deletecollection)
                    ))
                
                # executemany is efficient for multiple inserts
                cursor.executemany(insert_query, data_to_insert)

            # Step 3: Commit the transaction
            conn.commit()
            return True

    except sqlite3.IntegrityError as e:
        # This typically catches UNIQUE constraint violations (e.g., duplicate profile_id, resource)
        # or FOREIGN KEY constraint violations (e.g., if profile_id doesn't exist in profiles table,
        # and this check wasn't done upfront).
        if conn:
            conn.rollback() # Rollback changes if any part of the transaction failed
        # Log the error
        print(f"Database IntegrityError for profile_id {profile_id} during permission sync: {e}")
        return False
    except Exception as e:
        if conn:
            conn.rollback()
        # Log the error
        print(f"An unexpected error occurred while saving permissions for profile_id {profile_id}: {e}")
        return False


def get_permissions_list(profile_id: int) -> List[Permission]:
    """
    Retrieves a list of all permissions associated with a given profile_id.
    Returns a list of Permission Pydantic models.
    """
    permissions_out_list: List[Permission] = []
    # Optional: Validate if the profile_id exists first.
    # If profile_id does not exist, this function will correctly return an empty list.
    # if get_profile(profile_id) is None:
    #     # print(f"Warning: Profile with ID {profile_id} not found when fetching permissions.")
    #     return permissions_out_list # Return empty list

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Ensure conn.row_factory = sqlite3.Row is set in get_db_connection
            # for dict(row) to work and for easy access to columns by name.
            # If not, you'd access by index: row[0], row[1], etc.

            # Select all relevant fields from the permissions table
            # The Permission Pydantic model includes 'id' and 'profile_id'
            cursor.execute("""
                SELECT id, profile_id, resource, resource_api, resource_namespaced,
                       is_verb_get, is_verb_list, is_verb_watch,
                       is_verb_create, is_verb_update, is_verb_patch,
                       is_verb_delete, is_verb_deletecollection
                FROM permissions
                WHERE profile_id = ?
            """, (profile_id,))

            rows = cursor.fetchall()

            for row in rows:
                # Convert the database row (which is likely an sqlite3.Row object
                # if row_factory is set, or a tuple) into a dictionary.
                # Then, convert SQLite's 0/1 for booleans back to Python's True/False.
                row_dict = dict(row)
                permission_data = {
                    "id": row_dict["id"],
                    "profile_id": row_dict["profile_id"],
                    "resource": row_dict["resource"],
                    "resource_api": row_dict["resource_api"],
                    "resource_namespaced": bool(row_dict["resource_namespaced"]),
                    "is_verb_get": bool(row_dict["is_verb_get"]),
                    "is_verb_list": bool(row_dict["is_verb_list"]),
                    "is_verb_watch": bool(row_dict["is_verb_watch"]),
                    "is_verb_create": bool(row_dict["is_verb_create"]),
                    "is_verb_update": bool(row_dict["is_verb_update"]),
                    "is_verb_patch": bool(row_dict["is_verb_patch"]),
                    "is_verb_delete": bool(row_dict["is_verb_delete"]),
                    "is_verb_deletecollection": bool(row_dict["is_verb_deletecollection"]),
                }
                permissions_out_list.append(Permission(**permission_data))
            
            return permissions_out_list

    except sqlite3.Error as e:
        # Log the database error
        print(f"SQLite error while fetching permissions for profile_id {profile_id}: {e}")
        return [] # Return an empty list in case of DB error to avoid crashing
    except Exception as e:
        # Log any other unexpected errors
        print(f"An unexpected error occurred while fetching permissions for profile_id {profile_id}: {e}")
        return [] # Return an empty list


def get_user_aggregated_permissions(user_id: int) -> List[Dict[str, any]]:
    # Key: (resource_name, resource_api, resource_namespaced, namespace), Value: set of verbs
    aggregated_permissions: Dict[tuple[str, Optional[str], bool, str], Set[str]] = {}

    # Verb column names in the 'permissions' table and their corresponding string representation
    verb_mapping = {
        "is_verb_get": "get",
        "is_verb_list": "list",
        "is_verb_watch": "watch",
        "is_verb_create": "create",
        "is_verb_update": "update",
        "is_verb_patch": "patch",
        "is_verb_delete": "delete",
        "is_verb_deletecollection": "deletecollection",
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Fetch all permissions for all profiles associated with the user_id
            # This query joins users_has_profiles with permissions
            # It's generally more efficient to do this in one query rather than multiple.
            query = """
                SELECT
                    p.resource,
                    p.resource_api,
                    p.resource_namespaced,
                    upn.namespace,
                    p.is_verb_get,
                    p.is_verb_list,
                    p.is_verb_watch,
                    p.is_verb_create,
                    p.is_verb_update,
                    p.is_verb_patch,
                    p.is_verb_delete,
                    p.is_verb_deletecollection
                FROM permissions p
                JOIN users_has_profiles_namespaces upn ON p.profile_id = upn.profile_id
                WHERE upn.user_id = ?
            """
            cursor.execute(query, (user_id,))
            permission_rows = cursor.fetchall()

            # Step 2: Aggregate permissions
            for row in permission_rows:
                row_dict = dict(row) # Assumes conn.row_factory = sqlite3.Row
                resource_name = row_dict['resource']
                resource_api = row_dict['resource_api']
                resource_namespaced = bool(row_dict['resource_namespaced'])
                namespace = row_dict['namespace']

                aggregation_key = (resource_name, resource_api, resource_namespaced, namespace)

                if aggregation_key not in aggregated_permissions:
                    aggregated_permissions[aggregation_key] = set()

                for db_verb_col, verb_str in verb_mapping.items():
                    if row_dict.get(db_verb_col): # Checks if the verb (e.g., is_verb_get) is true (1)
                        aggregated_permissions[aggregation_key].add(verb_str)

        # Step 3: Format the aggregated permissions into the desired output structure
        output_list = []
        for (resource, resource_api, resource_namespaced, namespace), verbs_set in aggregated_permissions.items():
            output_list.append({
                "resource": resource,
                "resource_api": resource_api,
                "resource_namespaced": resource_namespaced,
                "namespace": namespace,
                "verbs": sorted(list(verbs_set)) # Sort verbs for consistent output
            })

        # Optional: Sort the final list by resource name for consistent output
        output_list.sort(key=lambda x: (x['namespace'], x['resource']))

        return output_list

    except sqlite3.Error as e:
        print(f"SQLite error while fetching aggregated permissions for user_id {user_id}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while fetching aggregated permissions for user_id {user_id}: {e}")
        return []