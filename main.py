import tkinter as tk
from tkinter import messagebox
# ADDED: Import config and app_logger
import config
from app_logger import app_logger

from logger import Logger
from tracker import WindowTracker
from ui import TimeTrackerUI
from graph import GraphDisplay
from themes import Theme
from utils import check_if_file_is_open # CORRECTED: check_if_file_is_open might need path from config
import time
import os # For checking icon file existence

def main():
    # ADDED: Ensure directories exist at the very start
    try:
        config.ensure_directories_exist()
        app_logger.info("Successfully checked/created necessary directories.")
    except Exception as e:
        app_logger.error(f"Failed to create necessary directories: {e}", exc_info=True)
        messagebox.showerror("Startup Error", f"Failed to create directories: {e}\nPlease check permissions or configuration.")
        return

    app_logger.info("Time Tracker application starting...")

    # CORRECTED: Use configured path for check_if_file_is_open
    if not check_if_file_is_open(str(config.MAIN_LOG_FILE_PATH)):
        app_logger.warning(f"Main log file {config.MAIN_LOG_FILE_PATH} is open or inaccessible. Exiting.")
        return

    root = tk.Tk()
    theme = Theme()

    # CORRECTED: Pass configured path to Logger
    try:
        logger_instance = Logger(str(config.MAIN_LOG_FILE_PATH), theme)
    except Exception as e:
        app_logger.error(f"Failed to initialize Logger: {e}", exc_info=True)
        messagebox.showerror("Initialization Error", f"Failed to initialize logger: {e}")
        root.destroy()
        return

    tracker = WindowTracker(logger_instance, logger_instance.log_activity, logger_instance.category_map)
    graph_display = GraphDisplay(logger_instance, theme)
    ui = TimeTrackerUI(root, tracker, graph_display, theme, logger_instance)

    app_logger.info("Core components initialized.")
    tracker.start_tracking()
    app_logger.info("Window tracking started.")

    def on_closing():
        """Handles the window close event."""
        app_logger.info("Close button clicked. Initiating close_program sequence.")
        ui.close_program()

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close event

    try:
        root.mainloop()
    except Exception as e:
        app_logger.critical(f"Unhandled exception in Tkinter mainloop: {e}", exc_info=True)
    finally:
        app_logger.info("Application exited.")


if __name__ == "__main__":
    main()