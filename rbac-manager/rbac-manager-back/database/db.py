# core/db.py
import sqlite3
import os
from contextlib import contextmanager

# --- DATABASE_URL ---
# Points to your pre-existing database file.
# Python will NOT attempt to create this file or its directory if they don't exist.
# If this file doesn't exist when sqlite3.connect() is called, it WILL create an empty one
# unless you take specific measures (which are more complex than just connecting).
# The key here is that *we* won't add logic to create parent directories or tables.
DATABASE_URL = os.getenv('RBAC_DB_SQLITE3_PATH')

@contextmanager
def get_db_connection():
    """
    Provides a database connection context.
    Assumes the database file and necessary tables ALREADY EXIST.
    """
    conn = None
    # Before connecting, check if the database file exists.
    # If not, we will raise an error as per the requirement not to create it.
    if not os.path.exists(DATABASE_URL):
        # If the directory for the DB doesn't exist, os.path.exists(DATABASE_URL) will be false.
        db_dir = os.path.dirname(DATABASE_URL)
        if not os.path.exists(db_dir):
            raise FileNotFoundError(
                f"Database directory does not exist: {db_dir}. "
                "Application will not create it."
            )
        raise FileNotFoundError(
            f"Database file does not exist: {DATABASE_URL}. "
            "Application will not create it."
        )

    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        yield conn
    except sqlite3.Error as e:
        # Catch potential errors during connection, e.g., if the file is not a valid DB
        print(f"SQLite error during connection: {e}")
        raise # Re-raise the exception to stop the application or be handled upstream
    finally:
        if conn:
            conn.close()

# The init_db_command function is REMOVED as per your request.
# Any if __name__ == "__main__": block related to initializing the DB is also removed.