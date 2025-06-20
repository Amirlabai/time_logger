# migrate_csv_to_sqlite.py
import pandas as pd
import sqlite3
import os
from pathlib import Path
import time
import config # Your project's config
# from app_logger import app_logger # If you want to use the same logger
# from db_utils import initialize_database, get_db_connection # Or direct connect

# --- SQL Escaping Helper ---
def escape_sql_string(value):
    """Simple SQL string escaper for values to be inserted."""
    if value is None:
        return "NULL"
    # Replace single quotes with two single quotes
    return str(value).replace("'", "''")

# --- Configuration for Migration ---
# Manually ensure config.py points to where your CSVs and new DB will be.
DB_PATH = config.DATABASE_FILE_PATH
MAIN_LOG_FILE = config.MAIN_LOG_FILE_PATH
HISTORICAL_LOG_DIR = config.HISTORICAL_LOG_DIR_PATH
USER_PROGRAMS_JSON = config.USER_PROGRAMS_FILE_PATH # Path to user_programs.json

def migrate_program_categories(conn_unused): # conn is no longer used
    print(f"Generating INSERTs for program categories from {USER_PROGRAMS_JSON}...")
    import json
    sql_statements = []
    try:
        with open(USER_PROGRAMS_JSON, "r") as f:
            category_map = json.load(f)

        for program_name, category in category_map.items():
            program_name_escaped = escape_sql_string(program_name)
            category_escaped = escape_sql_string(category)
            sql = f"INSERT OR IGNORE INTO program_categories (program_name, category) VALUES ('{program_name_escaped}', '{category_escaped}');"
            sql_statements.append(sql)

        print(f"Generated {len(sql_statements)} INSERT statements for program categories.")
    except FileNotFoundError:
        print(f"Warning: {USER_PROGRAMS_JSON} not found. Skipping category INSERT generation.")
    except Exception as e:
        print(f"Error generating category INSERTs: {e}")
    return sql_statements


def migrate_csv_file_to_db(csv_path, conn_unused): # conn is no longer used
    print(f"Generating INSERTs for data from {csv_path}...")
    sql_statements = []
    try:
        df = pd.read_csv(csv_path, dtype={'date': str}) # Keep date as string
        if df.empty:
            print(f"Skipping empty file: {csv_path}")
            return [] # Return empty list

        # Ensure all columns exist, add if missing to match DB expectations
        # These are based on the Logger's CSV format
        expected_cols = ["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None # Or appropriate default

        raw_rows_to_insert = []
        for _, row in df.iterrows():
            try:
                # Combine date and time strings to create datetime objects, then get epoch
                start_dt_str = f"{row['date']} {row['start_time']}"
                end_dt_str = f"{row['date']} {row['end_time']}"

                start_epoch = time.mktime(time.strptime(start_dt_str, '%d/%m/%Y %H:%M:%S'))
                end_epoch = time.mktime(time.strptime(end_dt_str, '%d/%m/%Y %H:%M:%S'))

                percent_text = row.get('percent', '0%') if pd.notna(row.get('percent')) else '0%'

                raw_rows_to_insert.append((
                    row['date'], row['program'], row['window'], row['category'],
                    row['start_time'], row['end_time'], float(row['total_time']) if pd.notna(row['total_time']) else 0.0,
                    start_epoch, end_epoch, percent_text
                ))
            except Exception as e:
                print(f"Skipping row due to parsing error: {row.to_dict()}. Error: {e}")
                continue

        if raw_rows_to_insert:
            for r_row in raw_rows_to_insert:
                # SQL escaping for string fields
                date_text_val = f"'{escape_sql_string(r_row[0])}'" if r_row[0] is not None else "NULL"
                program_name_val = f"'{escape_sql_string(r_row[1])}'" if r_row[1] is not None else "NULL"
                window_title_val = f"'{escape_sql_string(r_row[2])}'" if r_row[2] is not None else "NULL"
                category_val = f"'{escape_sql_string(r_row[3])}'" if r_row[3] is not None else "NULL"
                start_time_text_val = f"'{escape_sql_string(r_row[4])}'" if r_row[4] is not None else "NULL"
                end_time_text_val = f"'{escape_sql_string(r_row[5])}'" if r_row[5] is not None else "NULL"
                total_time_minutes_val = r_row[6] # Numeric
                start_timestamp_epoch_val = r_row[7] # Numeric
                end_timestamp_epoch_val = r_row[8] # Numeric
                percent_text_val = f"'{escape_sql_string(r_row[9])}'" if r_row[9] is not None else "NULL"

                sql = (f"INSERT INTO time_entries (date_text, program_name, window_title, category, "
                       f"start_time_text, end_time_text, total_time_minutes, start_timestamp_epoch, "
                       f"end_timestamp_epoch, percent_text) VALUES ({date_text_val}, {program_name_val}, "
                       f"{window_title_val}, {category_val}, {start_time_text_val}, {end_time_text_val}, "
                       f"{total_time_minutes_val}, {start_timestamp_epoch_val}, {end_timestamp_epoch_val}, "
                       f"{percent_text_val});")
                sql_statements.append(sql)

            print(f"Generated {len(sql_statements)} INSERT statements from {csv_path}.")
        return sql_statements

    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return []
    except pd.errors.EmptyDataError:
        print(f"Skipping empty or invalid CSV: {csv_path}")
        return []
    except Exception as e:
        print(f"Error processing {csv_path} for INSERT generation: {e}")
        return [] # Return empty list on error

def main_migration():
    print("Starting generation of SQL INSERT statements from CSV data...")
    all_sql_statements = []

    # 0. Database table creation is assumed to be handled by the main application's
    # db_utils.initialize_database() or similar. This script now only generates data INSERTs.
    # DB_PATH.parent.mkdir(parents=True, exist_ok=True) # SKIPPED
    # conn = sqlite3.connect(DB_PATH) # SKIPPED
    # ... (table creation SQL) ...
    # print("Database table creation skipped; assumed to be handled elsewhere.")


    # 1. Generate INSERTs for program_categories.json
    category_inserts = migrate_program_categories(None) # Pass None, conn not used
    all_sql_statements.extend(category_inserts)

    # 2. Generate INSERTs for main log file
    total_inserts_generated = 0 # This will count only data rows, not categories
    if MAIN_LOG_FILE.exists():
        main_log_inserts = migrate_csv_file_to_db(MAIN_LOG_FILE, None) # Pass None
        all_sql_statements.extend(main_log_inserts)
        total_inserts_generated += len(main_log_inserts)
    else:
        print(f"Main log file {MAIN_LOG_FILE} not found. Skipping its INSERT generation.")

    # 3. Generate INSERTs for historical log files
    if HISTORICAL_LOG_DIR.exists():
        for csv_file in HISTORICAL_LOG_DIR.glob("*.csv"):
            historical_log_inserts = migrate_csv_file_to_db(csv_file, None) # Pass None
            all_sql_statements.extend(historical_log_inserts)
            total_inserts_generated += len(historical_log_inserts)
    else:
        print(f"Historical log directory {HISTORICAL_LOG_DIR} not found. Skipping their INSERT generation.")

    output_sql_file_path = Path("prod/code/migration_inserts.sql")
    try:
        with open(output_sql_file_path, "w") as f:
            for stmt in all_sql_statements:
                f.write(stmt + "\n")
        print(f"\nSuccessfully wrote {len(all_sql_statements)} SQL INSERT statements to {output_sql_file_path}")
        print(f"Total data rows processed for INSERT generation: {total_inserts_generated} (excluding categories)")
    except Exception as e:
        print(f"Error writing SQL statements to {output_sql_file_path}: {e}")


if __name__ == "__main__":
    print("Starting data migration: CSV to SQL INSERT statements file...")
    # Make sure your config.py has the correct paths set up.
    main_migration()
