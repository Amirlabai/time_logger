"""SQLite connection and schema."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from utils import config
from utils.app_logger import app_logger

DATABASE_PATH = config.DATABASE_FILE_PATH


@contextmanager
def get_db_connection():
    conn = None
    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        app_logger.debug(f"Database connection established to {DATABASE_PATH}")
        yield conn
        conn.commit()
    except sqlite3.Error:
        if conn:
            conn.rollback()
        app_logger.error(
            f"Error in database connection {DATABASE_PATH}", exc_info=True
        )
        raise
    finally:
        if conn:
            conn.close()
            app_logger.debug(f"Database connection closed: {DATABASE_PATH}")


def create_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
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
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries (date_text);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_time_entries_start_epoch ON time_entries (start_timestamp_epoch);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_time_entries_program ON time_entries (program_name);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_time_entries_category ON time_entries (category);"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS program_categories (
                program_name TEXT PRIMARY KEY,
                category TEXT NOT NULL
            );
            """
        )
        conn.commit()
        app_logger.info("Database tables ensured to exist.")
    finally:
        cursor.close()


def initialize_database() -> None:
    app_logger.info(f"Initializing database at: {DATABASE_PATH}")
    with get_db_connection() as conn:
        create_tables(conn)
