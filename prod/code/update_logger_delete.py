# migrate_csv_to_sqlite.py
import pandas as pd
import sqlite3
import os
from pathlib import Path
import time
import config # Your project's config
# from app_logger import app_logger # If you want to use the same logger
# from db_utils import initialize_database, get_db_connection # Or direct connect

# --- Configuration for Migration ---
# Manually ensure config.py points to where your CSVs and new DB will be.
DB_PATH = config.DATABASE_FILE_PATH
MAIN_LOG_FILE = config.MAIN_LOG_FILE_PATH
HISTORICAL_LOG_DIR = config.HISTORICAL_LOG_DIR_PATH
USER_PROGRAMS_JSON = config.USER_PROGRAMS_FILE_PATH # Path to user_programs.json

def migrate_program_categories(conn):
    print(f"Migrating program categories from {USER_PROGRAMS_JSON}...")
    import json
    try:
        with open(USER_PROGRAMS_JSON, "r") as f:
            category_map = json.load(f)
        
        cursor = conn.cursor()
        for program_name, category in category_map.items():
            cursor.execute("INSERT OR IGNORE INTO program_categories (program_name, category) VALUES (?, ?)",
                           (program_name, category))
        conn.commit()
        print(f"Migrated {len(category_map)} program categories.")
    except FileNotFoundError:
        print(f"Warning: {USER_PROGRAMS_JSON} not found. Skipping category migration.")
    except Exception as e:
        print(f"Error migrating program categories: {e}")
        if conn: conn.rollback()


def migrate_csv_file_to_db(csv_path, conn):
    print(f"Migrating data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path, dtype={'date': str}) # Keep date as string
        if df.empty:
            print(f"Skipping empty file: {csv_path}")
            return 0
        
        # Ensure all columns exist, add if missing to match DB expectations
        # These are based on the Logger's CSV format
        expected_cols = ["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None # Or appropriate default
        
        # We need start_timestamp_epoch and end_timestamp_epoch for the DB.
        # Original CSV has date, start_time, end_time strings.
        
        rows_to_insert = []
        for _, row in df.iterrows():
            try:
                # Combine date and time strings to create datetime objects, then get epoch
                start_dt_str = f"{row['date']} {row['start_time']}"
                end_dt_str = f"{row['date']} {row['end_time']}"
                
                start_epoch = time.mktime(time.strptime(start_dt_str, '%d/%m/%Y %H:%M:%S'))
                end_epoch = time.mktime(time.strptime(end_dt_str, '%d/%m/%Y %H:%M:%S'))

                # Handle missing 'percent' if it was not always there
                percent_text = row.get('percent', '0%') if pd.notna(row.get('percent')) else '0%'


                rows_to_insert.append((
                    row['date'], row['program'], row['window'], row['category'],
                    row['start_time'], row['end_time'], float(row['total_time']),
                    start_epoch, end_epoch, percent_text
                ))
            except Exception as e:
                print(f"Skipping row due to parsing error: {row.to_dict()}. Error: {e}")
                continue
        
        if rows_to_insert:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO time_entries 
                (date_text, program_name, window_title, category, 
                 start_time_text, end_time_text, total_time_minutes, 
                 start_timestamp_epoch, end_timestamp_epoch, percent_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows_to_insert)
            conn.commit()
            print(f"Migrated {len(rows_to_insert)} rows from {csv_path}.")
            return len(rows_to_insert)
        return 0

    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return 0
    except pd.errors.EmptyDataError:
        print(f"Skipping empty or invalid CSV: {csv_path}")
        return 0
    except Exception as e:
        print(f"Error processing {csv_path}: {e}")
        if conn: conn.rollback()
        return 0

def main_migration():
    # 0. Initialize DB (create tables) - if not already done by app startup logic
    # For a standalone script, better to ensure it's done here.
    # (Using direct connect for simplicity in standalone script)
    conn = None
    try:
        # Create/Connect to DB
        DB_PATH.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        conn = sqlite3.connect(DB_PATH)
        
        # Create tables (from db_utils.py logic, simplified here)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT, date_text TEXT NOT NULL, program_name TEXT NOT NULL,
                window_title TEXT, category TEXT NOT NULL, start_time_text TEXT NOT NULL,
                end_time_text TEXT NOT NULL, total_time_minutes REAL NOT NULL,
                start_timestamp_epoch REAL NOT NULL, end_timestamp_epoch REAL NOT NULL, percent_text TEXT DEFAULT '0%'
            );""")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries (date_text);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_start_epoch ON time_entries (start_timestamp_epoch);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_program ON time_entries (program_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_category ON time_entries (category);")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS program_categories (
                program_name TEXT PRIMARY KEY, category TEXT NOT NULL
            );""")
        conn.commit()
        print("Database tables ensured.")

        # 1. Migrate program_categories.json
        migrate_program_categories(conn)

        # 2. Migrate main log file
        total_migrated = 0
        if MAIN_LOG_FILE.exists():
            total_migrated += migrate_csv_file_to_db(MAIN_LOG_FILE, conn)
        else:
            print(f"Main log file {MAIN_LOG_FILE} not found. Skipping.")

        # 3. Migrate historical log files
        if HISTORICAL_LOG_DIR.exists():
            for csv_file in HISTORICAL_LOG_DIR.glob("*.csv"):
                total_migrated += migrate_csv_file_to_db(csv_file, conn)
        else:
            print(f"Historical log directory {HISTORICAL_LOG_DIR} not found. Skipping.")
        
        print(f"\nMigration complete. Total log entries migrated: {total_migrated}")

    except Exception as e:
        print(f"A critical error occurred during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting data migration from CSV to SQLite...")
    # Make sure your config.py has the correct paths set up.
    main_migration()