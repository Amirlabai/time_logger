import time
import win32gui
import win32process
import psutil
import threading
import traceback
from logger import Logger
import themes

class WindowTracker:
    def __init__(self, log_activity_callback, category_map):
        self.log_activity = log_activity_callback
        self.category_map = category_map
        self.running = True
        self.active_window = None
        self.start_time = 0
        self.perv_window = None

    def get_active_window(self):
        hwnd = win32gui.GetForegroundWindow()
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().replace(".exe", "")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return "Unknown"
        except Exception:
            return "Unknown"

    def track_windows(self):
        try:
            while self.running:
                new_window = self.get_active_window()
                if new_window and new_window != self.active_window:
                    if self.active_window:
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        self.log_activity(self.active_window, self.start_time, end_time, total_time)
                        self.perv_window = self.active_window
                    if new_window not in self.category_map:
                        category = self.get_category(new_window)
                        if category:
                            self.category_map[new_window] = category
                    self.perv_window = self.active_window
                    self.active_window = new_window
                    self.start_time = time.time()
                time.sleep(1)
        except Exception as e:
            print(f"Error in window_tracker thread: {e}")
            traceback.print_exc()

    def start_tracking(self):
        thread = threading.Thread(target=self.track_windows)
        thread.daemon = True
        thread.start()

    def get_category(self, window_name):
        #call to logger.get_category.
        return Logger("time_log.csv",themes).get_category(window_name)

    def stop_tracking(self):
        self.running = False