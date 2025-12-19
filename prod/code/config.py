# config.py
import os
from pathlib import Path
import sys

# --- Base Project Directory ---
def find_project_root(marker_filename=".project_root"):
    """
    Finds the project root by searching upwards for a marker file.
    """
    current_path = None

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # For bundled executables, _MEIPASS is often the effective root
        # or where extracted data resides. Adjust if your actual project root
        # is relative to this (e.g., if you have a "src" subfolder within _MEIPASS).
        current_path = Path(sys._MEIPASS).resolve()
    else:
        try:
            # Start from the current script's directory
            current_path = Path(__file__).parent.resolve()
        except NameError:
            # Fallback for interactive environments
            current_path = Path.cwd().resolve()

    # Iterate upwards until the marker file is found or we hit the root
    for parent in [current_path] + list(current_path.parents):
        if (parent / marker_filename).exists():
            return parent
    
    # If not found, fall back to a reasonable default or raise an error
    print(f"Warning: Project root marker '{marker_filename}' not found. "
          f"Falling back to initial path: {current_path}")
    return current_path # Or raise FileNotFoundError("Project root marker not found!")

PROJECT_ROOT = find_project_root()

PROJECT_LIB = PROJECT_ROOT / "prod/lib"
# --- Log Directories and Files ---
LOG_BASE_DIR_NAME = "timeLog" # Name of the main logging directory
LOG_BASE_DIR = PROJECT_ROOT / PROJECT_LIB / LOG_BASE_DIR_NAME # Base directory for all logs (e.g., C:\YourProject\timeLog)

# --- Paths for Data Migration Script (migrate_data_to_sqlite.py) ---
# The following paths are used by the one-time migration script.
# They are no longer actively used by the main application.
#MAIN_LOG_FILE_NAME = "time_log.csv"
#HISTORICAL_LOG_DIR_NAME = "log" # Subdirectory for archived CSV logs
REPORTS_DIR_NAME = "report" # Subdirectory for monthly reports

DATABASE_FILE_NAME = "time_tracker_data.sqlite"
DATABASE_FILE_PATH = LOG_BASE_DIR / DATABASE_FILE_NAME # Or PROJECT_ROOT if preferred

# Construct full paths
#MAIN_LOG_FILE_PATH = LOG_BASE_DIR / MAIN_LOG_FILE_NAME
#HISTORICAL_LOG_DIR_PATH = LOG_BASE_DIR / HISTORICAL_LOG_DIR_NAME
REPORTS_DIR_PATH = LOG_BASE_DIR / REPORTS_DIR_NAME

# --- User Data Files ---
#USER_PROGRAMS_FILE_NAME = "user_programs.json"
#USER_PROGRAMS_FILE_PATH = PROJECT_ROOT / USER_PROGRAMS_FILE_NAME # Stored in project root

# --- Icon Paths ---
# Store icons in an 'icons' folder in the project root
ICON_DIR_NAME = "icons"
ICON_DIR_PATH = PROJECT_ROOT / PROJECT_LIB / ICON_DIR_NAME
TIMER_ICON_NAME = "timer_icon_32.ico"
BARCHART_ICON_NAME = "barchart_32.ico"
RUN_IMAGE_PATH = "play.png"
PAUSE_IMAGE_PATH = "pause.png"

TIMER_ICON_PATH = ICON_DIR_PATH / TIMER_ICON_NAME
BARCHART_ICON_PATH = ICON_DIR_PATH / BARCHART_ICON_NAME
RUN_IMAGE_PATH = ICON_DIR_PATH / RUN_IMAGE_PATH
PAUSE_IMAGE_PATH = ICON_DIR_PATH / PAUSE_IMAGE_PATH

# --- Application Settings ---
DEFAULT_BREAK_TIME_SECONDS = 3000  # 50 minutes
MIN_BREAK_TIME_SECONDS = 600 # 10 minutes


# --- Function to ensure directories exist ---
def ensure_directories_exist():
    """Creates necessary log directories if they don't exist."""
    dirs_to_create = [
        LOG_BASE_DIR,
        REPORTS_DIR_PATH,
        ICON_DIR_PATH # Also ensure icon dir path is considered, though icons should be pre-existing
    ]
    for dir_path in dirs_to_create:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # This error should be logged by the app_logger once it's initialized
            # For now, print to stderr as a fallback if this runs before logger setup
            print(f"Error creating directory {dir_path}: {e}")
            # Depending on severity, you might want to raise the exception
            # or handle it more gracefully (e.g., disable features that need the dir)

if __name__ == "__main__":
    # Example of how to use and print paths
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Log Base Directory: {LOG_BASE_DIR}")
    #print(f"Main Log File: {MAIN_LOG_FILE_PATH}")
    #print(f"Historical Log Dir: {HISTORICAL_LOG_DIR_PATH}")
    print(f"Reports Dir: {REPORTS_DIR_PATH}")
    #print(f"User Programs File: {USER_PROGRAMS_FILE_PATH}")
    print(f"Timer Icon: {TIMER_ICON_PATH}")
    print(f"Barchart Icon: {BARCHART_ICON_PATH}")
    ensure_directories_exist()
    print("Directories checked/created.")