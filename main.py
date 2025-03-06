import tkinter as tk
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
    theme = Theme()  # Initialize theme
    logger = Logger("time_log.csv",theme)
    tracker = WindowTracker(logger.log_activity, logger.category_map)
    graph_display = GraphDisplay(logger, theme)
    ui = TimeTrackerUI(root, tracker, graph_display, theme, logger)

    tracker.start_tracking()
    root.mainloop()

if __name__ == "__main__":
    main()