# app_logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Use a path relative to this file's location or a more absolute path from config
# For simplicity, let's place it in the project root for now.
try:
    LOG_FILE_PATH = Path(__file__).parent.resolve() / "time_tracker_app.log"
except NameError:
    LOG_FILE_PATH = Path.cwd() / "time_tracker_app.log"

# Configure the root logger
# You can also get a specific logger: logger = logging.getLogger("TimeTrackerApp")

def setup_logger():
    logger = logging.getLogger("TimeTrackerApp")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of messages

    # Prevent multiple handlers if setup_logger is called more than once
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Log INFO and above to console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    # Ensure the directory for the log file exists if it's not the project root
    try:
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1024*1024*5, backupCount=2) # 5MB per file, 2 backups
        file_handler.setLevel(logging.DEBUG) # Log DEBUG and above to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Failed to set up file handler for logging: {e}", exc_info=True)


    # Initial log message
    # logger.info("Logger initialized.") # This might be too early if config isn't fully loaded
    return logger

# Initialize logger when this module is imported
app_logger = setup_logger()

if __name__ == '__main__':
    app_logger.debug("This is a debug message.")
    app_logger.info("This is an info message.")
    app_logger.warning("This is a warning message.")
    app_logger.error("This is an error message.")
    app_logger.critical("This is a critical message.")
    try:
        1/0
    except ZeroDivisionError:
        app_logger.exception("A ZeroDivisionError occurred!")