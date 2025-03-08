import tkinter as tk
from tkinter import messagebox
from logger import Logger
from tracker import WindowTracker
from ui import TimeTrackerUI
from graph import GraphDisplay
from themes import Theme
from utils import check_if_file_is_open

def main():
    if not check_if_file_is_open():
        return

    root = tk.Tk()
    theme = Theme()
    logger = Logger("time_log.csv",theme)
    tracker = WindowTracker(logger.log_activity, logger.category_map)
    graph_display = GraphDisplay(logger, theme)
    ui = TimeTrackerUI(root, tracker, graph_display, theme, logger)

    tracker.start_tracking()

    def on_closing():
        """Handles the window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            tracker.stop_tracking()  # Stop the tracker
            # Perform any other cleanup (e.g., saving data, closing files)
            root.destroy()  # Close the window

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close event

    root.mainloop()

if __name__ == "__main__":
    main()