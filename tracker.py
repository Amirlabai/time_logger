import time
import win32gui
import win32process
import psutil
import threading
import traceback
from logger import Logger  # Assuming you have a logger.py
import themes # And a themes.py
import json
from tkinter import messagebox

class WindowTracker:
    def __init__(self,logger, log_activity_callback, category_map, _break_time=3000):
        self.log_activity = log_activity_callback
        self.category_map = category_map
        self.running = True
        self.active_window = None
        self.total_time = 0
        self._break_time = _break_time
        self._break_time_counter = _break_time
        self.start_time = time.time()
        self.break_timer_start = time.time()
        self.perv_window = None
        self.thread = None  # Store the thread
        self.logger = logger

    @property
    def break_time_counter(self):
        time_frame = int(self._break_time_counter)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return str(f"{hours:02}:{minutes:02}:{seconds:02}")
    
    @break_time_counter.setter
    def break_time_counter(slef,other):
        if isinstance(other, int):
            return other
    
    @property
    def break_time(self):
        time_frame = int(self._break_time)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return str(f"{hours:02}:{minutes:02}:{seconds:02}")
    
    @break_time.setter
    def break_time(self,other):
        if isinstance(other, int) and other >= 600:
            self._break_time = other
        else:
            messagebox.showerror("TOO LOW", "Set Break Yimer Higher Than 10 Minutes")
            self._break_time = 3000

    def get_active_window(self):
        hwnd = win32gui.GetForegroundWindow()
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name().replace(".exe", "")
            window_title = win32gui.GetWindowText(hwnd)
            return app_name, window_title
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error in get_active_window: {e}")
            return "Unknown", "blank" # Return empty string for window title
        except Exception as e:
            print(f"Error in get_active_window: {e}")
            traceback.print_exc()
            return "Unknown", "blank"

    def track_windows(self):
        try:
            while self.running:
                self._break_time_counter = self._break_time - (time.time() - self.break_timer_start)
                print(int(self._break_time_counter))
                if self._break_time_counter < 0:
                    self.break_time_counter = self.break_time
                    messagebox.showinfo("Break", "take a 10 min break bro")
                    self.break_timer_start = time.time()
                program_name, window_name = self.get_active_window()
                if program_name and program_name != self.active_window:
                    self.log_current_window_activity(window_name)  # Log previous window
                    if program_name not in self.category_map:
                        category = self.get_category(program_name)
                        if category:
                            self.category_map[program_name] = category
                    self.perv_window = self.active_window
                    self.active_window = program_name
                time.sleep(1)
            # Log the final window activity.
            self.update_user_data()
            self.log_current_window_activity(window_name)

        except Exception as e:
            print(f"Error in window_tracker thread: {e}")
            traceback.print_exc()

    def log_current_window_activity(self,window_name):
        if self.active_window:
            end_time = time.time()
            self.total_time = end_time - self.start_time
            self.log_activity(self.active_window, window_name, self.start_time, end_time, self.total_time)
            self.start_time = end_time

    def start_tracking(self):
        self.thread = threading.Thread(target=self.track_windows)
        self.thread.daemon = True
        self.thread.start()

    def get_category(self, window_name):
        # Use the class's logger instance
        return self.logger.get_category(window_name)

    def stop_tracking(self):
        self.running = False

    def update_user_data(self):
        with open('user_programs.txt', "w") as file:
            json.dump(self.logger.category_map, file)