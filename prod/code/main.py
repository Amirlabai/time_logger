import tkinter as tk
from tkinter import messagebox
import time # Keep for any general time usage, though not directly in this version of main
import os # Keep for path operations if any were here, though less direct use now
import sys # Keep for sys.path manipulations if they were more complex

# Project-specific imports
import config
from app_logger import app_logger # For application-wide logging

# Assuming db_utils.py contains the database initialization logic
# If initialize_database is in logger.py or config.py, adjust import accordingly.
# For this example, let's assume it's cleanly in a new db_utils module
try:
    import db_utils # This would contain initialize_database()
except ImportError:
    app_logger.warning("db_utils.py not found. Database might not be initialized if not handled elsewhere.")
    # As a fallback, if you decided to put initialize_database in logger.py:
    # from logger import initialize_database as initialize_db_from_logger
    # Or handle this more robustly based on your project structure.


from logger import Logger # The refactored Logger class
from tracker import WindowTracker
from ui import TimeTrackerUI
from graph import GraphDisplay
from themes import Theme
# utils.check_if_file_is_open is no longer needed here for the main log file.
# Keep utils if other utility functions are used.
# from utils import some_other_utility # Example

def main():
    # 1. Ensure general application directories exist (icons, parent log/DB dir)
    # This is still important. config.py defines where the DB might be stored (e.g., under LOG_BASE_DIR)
    try:
        config.ensure_directories_exist()
        app_logger.info("Successfully checked/created necessary application directories.")
    except Exception as e:
        app_logger.error(f"Failed to create necessary application directories: {e}", exc_info=True)
        messagebox.showerror("Startup Error", f"Failed to create application directories: {e}\nPlease check permissions or configuration.")
        return

    # 2. Initialize the SQLite Database (Create tables if they don't exist)
    # This should happen BEFORE Logger or any other component tries to access the DB.
    try:
        # Assuming initialize_database() is in db_utils
        if 'db_utils' in sys.modules and hasattr(db_utils, 'initialize_database'):
            db_utils.initialize_database() 
            app_logger.info("Database initialization sequence completed.")
        # elif 'initialize_db_from_logger' in locals(): # Example if imported from logger
            # initialize_db_from_logger()
            # app_logger.info("Database (via logger module) initialization sequence completed.")
        else:
            # This means the function wasn't found, which is a critical setup step.
            app_logger.critical("Database initialization function not found. Application cannot proceed safely.")
            messagebox.showerror("Startup Error", "Critical: Database initialization failed. Application will exit.")
            return
            
    except Exception as e:
        app_logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        messagebox.showerror("Startup Error", f"Failed to initialize database: {e}\nApplication will exit.")
        return

    app_logger.info("Time Tracker application starting...")

    # The check_if_file_is_open for the main CSV log is no longer needed,
    # as SQLite handles its own file access.

    root = tk.Tk()
    theme = Theme()

    # 3. Instantiate Logger (updated __init__ signature)
    try:
        # Logger now only takes theme, as DB path is from config
        logger_instance = Logger(theme) 
    except Exception as e:
        app_logger.error(f"Failed to initialize Logger: {e}", exc_info=True)
        messagebox.showerror("Initialization Error", f"Failed to initialize logger: {e}")
        root.destroy()
        return

    # Instantiate other components (these largely remain the same, as they depend on the Logger *instance*)
    try:
        # category_map is now an attribute of logger_instance, loaded from DB
        tracker = WindowTracker(logger_instance, logger_instance.log_activity, logger_instance.category_map)
        graph_display = GraphDisplay(logger_instance, theme) # Assuming GraphDisplay uses logger_instance to get data
        ui = TimeTrackerUI(root, tracker, graph_display, theme, logger_instance)
    except Exception as e:
        app_logger.error(f"Failed to initialize core application components: {e}", exc_info=True)
        messagebox.showerror("Initialization Error", f"Failed to initialize core components: {e}")
        root.destroy()
        return

    app_logger.info("Core components initialized.")
    
    try:
        tracker.start_tracking()
        app_logger.info("Window tracking started.")
    except Exception as e:
        app_logger.error(f"Failed to start window tracking: {e}", exc_info=True)
        messagebox.showerror("Runtime Error", f"Failed to start window tracking: {e}")
        root.destroy()
        return


    def on_closing():
        """Handles the window close event."""
        app_logger.info("Close button clicked. Initiating close_program sequence.")
        ui.close_program() # ui.close_program should handle tracker.stop_tracking()

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close event

    try:
        root.mainloop()
    except Exception as e:
        app_logger.critical(f"Unhandled exception in Tkinter mainloop: {e}", exc_info=True)
    finally:
        # Ensure tracker is stopped if mainloop exits unexpectedly,
        # though on_closing should ideally handle this for graceful exits.
        if tracker and tracker.is_running: # Check if tracker exists and is_running
            app_logger.info("Ensuring tracker is stopped due to mainloop exit.")
            tracker.stop_tracking()
        app_logger.info("Application exited.")


if __name__ == "__main__":
    # Basic sys.path manipulation if your 'prod' directory isn't directly on Python path
    # This might have been in your original main.py or handled by your IDE/environment
    # current_dir = Path(__file__).resolve().parent
    # prod_dir = current_dir.parent 
    # if str(prod_dir) not in sys.path:
    #    sys.path.insert(0, str(prod_dir))
    # if str(current_dir) not in sys.path: # If 'code' is not a package itself
    #    sys.path.insert(0, str(current_dir))


    # It's good practice to ensure app_logger is configured before any significant app logic.
    # app_logger itself should be importable.
    
    main()