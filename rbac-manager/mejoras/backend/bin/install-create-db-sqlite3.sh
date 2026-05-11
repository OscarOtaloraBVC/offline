-- backend/bin/install-create-db-sqlite3.sh (añadir)
CREATE TABLE certificate_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    days_before_expiration INTEGER NOT NULL,  -- 7, 15, 30, 60 días
    is_active INTEGER DEFAULT 1,
    last_notified_at TEXT,                    -- Última vez que se notificó
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, days_before_expiration)
);

-- Índices para consultas rápidas
CREATE INDEX idx_alerts_user_active ON certificate_alerts(user_id, is_active);
CREATE INDEX idx_alerts_notified ON certificate_alerts(last_notified_at);