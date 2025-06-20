import sqlite3
from pathlib import Path

# Assuming db_utils.py and config.py are in the same directory or accessible in PYTHONPATH
# To run this script directly for testing, you might need to adjust imports
# or ensure the 'prod/code' directory is in sys.path.
# For the agent's execution context, direct imports should work if files are in 'prod/code'.
try:
    from db_utils import get_db_connection, initialize_database
    import config # To resolve config.DATABASE_FILE_PATH if needed by db_utils
except ImportError:
    print("Error: Could not import db_utils or config. Make sure they are in the Python path.")
    print("If running standalone, ensure PYTHONPATH is set or script is in 'prod/code'.")
    exit(1)

SQL_FILE_PATH = Path(__file__).parent / "migration_inserts.sql"

def apply_sql_statements():
    print(f"Starting application of SQL statements from {SQL_FILE_PATH}...")

    if not SQL_FILE_PATH.exists():
        print(f"Error: SQL file not found at {SQL_FILE_PATH}")
        return

    # 1. Ensure database and tables are initialized
    try:
        print("Initializing database (ensuring tables exist)...")
        initialize_database()
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return

    conn = None
    statements_executed = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print(f"Connected to database: {config.DATABASE_FILE_PATH}")

        with open(SQL_FILE_PATH, "r") as f:
            sql_script = f.read()

        # Splitting statements by semicolon, but being careful about content.
        # sqlite3.executescript is generally better for running multiple statements.
        # For this specific case where each line is one INSERT, line-by-line is also fine.

        # Using executescript as it's designed for this.
        # Note: executescript implicitly commits or rollbacks on error.
        # If explicit commit is needed after all statements, then iterate and execute.

        # Let's execute line by line for better control and counting for this scenario
        lines = sql_script.splitlines()
        for line_num, sql_statement in enumerate(lines):
            sql_statement = sql_statement.strip()
            if sql_statement and not sql_statement.startswith('--'): # Ignore empty lines or comments
                try:
                    cursor.execute(sql_statement)
                    statements_executed += 1
                except sqlite3.Error as e:
                    print(f"Error executing SQL statement on line {line_num + 1}: {sql_statement}")
                    print(f"SQLite error: {e}")
                    # Decide if you want to stop on error or continue
                    # conn.rollback() # Rollback this statement if needed, or all at the end
                    # For now, we'll let it continue and report errors.

        conn.commit() # Commit all successful statements
        print(f"Successfully executed {statements_executed} SQL statements.")

    except sqlite3.Error as e:
        print(f"SQLite error during SQL application: {e}")
        if conn:
            conn.rollback()
    except FileNotFoundError:
        print(f"Error: SQL script file not found at {SQL_FILE_PATH}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # This is to make sure the script can find other project modules if run directly
    # For example, if 'prod/code' is not in PYTHONPATH
    import sys
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.append(str(current_dir))
    # If 'prod' is the root for 'code', then 'prod' needs to be in path for 'from code import'
    # However, db_utils and config are in the same directory, so direct imports should be fine.

    apply_sql_statements()
