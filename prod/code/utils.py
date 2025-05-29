import os
from tkinter import messagebox
from pathlib import Path

# ADDED:
from app_logger import app_logger
# import config # Not strictly needed here if paths are passed in

def check_if_file_is_open(file_path_str): # Parameter name changed for clarity
    """
    Checks if a file can be opened in append mode.
    This is a basic check for exclusivity if other programs lock files.
    """
    file_path = Path(file_path_str)
    app_logger.debug(f"Checking if file is open: {file_path}")
    try:
        # If the file doesn't exist, we can "open" it for append, it will be created.
        # The main concern is if it *does* exist and is locked.
        if file_path.exists():
            with open(file_path, "a"): # Try to open in append mode
                pass # Successfully opened and closed
        else:
            # If file doesn't exist, it's effectively not "open by another program" in a problematic way.
            # The logger will create it.
            app_logger.info(f"File {file_path} does not exist yet. It can be created.")
        return True
    except PermissionError:
        error_msg = f"Permission denied for file '{file_path}'. It might be open by another program or you lack permissions."
        app_logger.error(error_msg, exc_info=True)
        messagebox.showerror("File Access Error", error_msg)
        return False
    except IOError as e: # Catch other IOErrors too
        error_msg = f"File '{file_path}' is currently in use or inaccessible.\nDetails: {e}\nPlease close it and try again."
        app_logger.error(error_msg, exc_info=True) # Log full error
        messagebox.showerror("File In Use", error_msg)
        return False
    except Exception as e: # Catch any other unexpected errors
        error_msg = f"An unexpected error occurred while checking file '{file_path}': {e}"
        app_logger.error(error_msg, exc_info=True)
        messagebox.showerror("File Check Error", error_msg)
        return False

# ADDED: Function to ensure necessary directories (moved from config to be callable after logger setup if needed)
# This is also called in config.py directly. Having it here is for utility.
def ensure_app_directories(base_log_dir, historical_subdir, reports_subdir, icon_subdir):
    """Creates necessary application directories."""
    dirs_to_create = [
        base_log_dir,
        base_log_dir / historical_subdir,
        base_log_dir / reports_subdir,
        # Assuming icons are bundled, but useful if they could be generated/downloaded
        # Path(__file__).parent.resolve() / icon_subdir # Example for icons relative to project root
    ]
    for dir_path in dirs_to_create:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            app_logger.info(f"Directory ensured: {dir_path}")
        except OSError as e:
            app_logger.error(f"Error creating directory {dir_path}: {e}", exc_info=True)
            # Propagate or handle as critical startup error
            raise # Re-raise to indicate critical failure if needed by caller