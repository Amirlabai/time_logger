import tkinter as tk
from tkinter import messagebox
from logger import Logger
from tracker import WindowTracker
from ui import TimeTrackerUI
from graph import GraphDisplay
from themes import Theme
from utils import check_if_file_is_open
import time


def main():
    if not check_if_file_is_open("C:\\timeLog\\time_log.csv"):
        return

    root = tk.Tk()
    theme = Theme()
    logger = Logger("C:\\timeLog\\time_log.csv",theme)
    tracker = WindowTracker(logger.log_activity, logger.category_map)
    graph_display = GraphDisplay(logger, theme)
    ui = TimeTrackerUI(root, tracker, graph_display, theme, logger)

    tracker.start_tracking()

    def on_closing():
        """Handles the window close event."""
        ui.close_program()

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close event

    root.mainloop()

if __name__ == "__main__":
    main()