#!/bin/bash

FILEDB=/opt/rbac-manager/data/rbac-sqlite3.db

mkdir -p $(dirname "$FILEDB")
if [ -f "$FILEDB" ]; then
    echo "File $FILEDB was found"
else
    sqlite3 "$FILEDB" "CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        cert_days INTEGER NOT NULL,
        observations TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        state TEXT DEFAULT 'ENABLED' NOT NULL
    );"

    sqlite3 "$FILEDB" "CREATE TABLE profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL
    );"

    sqlite3 "$FILEDB" "CREATE TABLE users_has_profiles_namespaces(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        profile_id INTEGER NOT NULL,
        namespace TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    );"

    sqlite3 "$FILEDB" "CREATE TABLE permissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource TEXT NOT NULL,
        resource_api TEXT,
        resource_namespaced INTEGER DEFAULT 1,
        profile_id INTEGER NOT NULL,
        is_verb_get INTEGER DEFAULT 0,
        is_verb_list INTEGER DEFAULT 0,
        is_verb_watch INTEGER DEFAULT 0,
        is_verb_create INTEGER DEFAULT 0,
        is_verb_update INTEGER DEFAULT 0,
        is_verb_patch INTEGER DEFAULT 0,
        is_verb_delete INTEGER DEFAULT 0,
        is_verb_deletecollection INTEGER DEFAULT 0,
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    );"

    sqlite3 "$FILEDB" "CREATE TABLE users_certs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kubeconfig_content TEXT,
        objs_created TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );"

    # Tabla de alertas de expiración de certificados (UNA SOLA VEZ con todas las columnas)
    sqlite3 "$FILEDB" "CREATE TABLE certificate_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        days_before_expiration INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1,
        last_notified_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        notification_emails TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, days_before_expiration)
    );"

    # Índices para optimización de consultas
    sqlite3 "$FILEDB" "CREATE INDEX idx_alerts_user_active 
        ON certificate_alerts(user_id, is_active);"

    sqlite3 "$FILEDB" "CREATE INDEX idx_alerts_notified 
        ON certificate_alerts(last_notified_at);"

    sqlite3 "$FILEDB" "CREATE INDEX idx_alerts_emails 
        ON certificate_alerts(notification_emails);"

    sqlite3 "$FILEDB" ".tables"

    echo -e "\nOk!   :)\n"
fi