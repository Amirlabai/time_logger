# db_utils.py
import sqlite3
from pathlib import Path
import config # Assuming this is accessible
from app_logger import app_logger # Assuming this is accessible

DATABASE_PATH = config.DATABASE_FILE_PATH

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        # Ensure the directory for the database file exists
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        app_logger.debug(f"Database connection established to {DATABASE_PATH}")
    except sqlite3.Error as e:
        app_logger.error(f"Error connecting to database {DATABASE_PATH}: {e}", exc_info=True)
        raise # Or handle more gracefully depending on application needs
    return conn

def create_tables(conn):
    """Creates the necessary tables if they don't already exist."""
    try:
        cursor = conn.cursor()
        
        # Time Entries Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_text TEXT NOT NULL,
                program_name TEXT NOT NULL,
                window_title TEXT,
                category TEXT NOT NULL,
                start_time_text TEXT NOT NULL,
                end_time_text TEXT NOT NULL,
                total_time_minutes REAL NOT NULL,
                start_timestamp_epoch REAL NOT NULL,
                end_timestamp_epoch REAL NOT NULL,
                percent_text TEXT DEFAULT '0%' 
            );
        """)
        # Add an index on date_text and start_timestamp_epoch for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries (date_text);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_start_epoch ON time_entries (start_timestamp_epoch);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_program ON time_entries (program_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_category ON time_entries (category);")


        # Program Categories Table (replaces user_programs.json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS program_categories (
                program_name TEXT PRIMARY KEY,
                category TEXT NOT NULL
            );
        """)
        
        conn.commit()
        app_logger.info("Database tables ensured to exist.")
    except sqlite3.Error as e:
        app_logger.error(f"Error creating database tables: {e}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()

def initialize_database():
    """Initializes the database and creates tables if they don't exist."""
    app_logger.info(f"Initializing database at: {DATABASE_PATH}")
    conn = get_db_connection()
    if conn:
        create_tables(conn)
        conn.close()
    else:
        # This case should ideally be handled to prevent app from running without DB
        app_logger.critical("Failed to establish database connection during initialization.")

if __name__ == '__main__':
    # This can be run once to set up the DB, or called at app startup.
    initialize_database()
    # Example usage:
    # conn = get_db_connection()
    # if conn:
    #     # Do stuff
    #     conn.close()
    pass