import time
import win32gui
import win32process
import psutil
import threading
# import traceback # CORRECTED: Use logger instead of traceback directly
# from logger import Logger # CORRECTED: Not needed directly, logger instance passed in __init__
# import themes # CORRECTED: Not needed in tracker
import json
from tkinter import messagebox

# ADDED:
import config
from app_logger import app_logger


class WindowTracker:
    def __init__(self, logger_instance, log_activity_callback, category_map, break_time_seconds=None): # CORRECTED: logger_instance
        self.logger_instance = logger_instance # Store the passed logger object
        self.log_activity = log_activity_callback
        self.category_map = category_map # This is logger_instance.category_map, passed for direct access
        self.running = True
        self.active_window_exe = None # Store executable name
        self.active_window_title = None # Store window title
        
        self.current_session_total_time_seconds = 0 # Time spent in current self.active_window_exe
        
        if break_time_seconds is None:
            self._break_time = config.DEFAULT_BREAK_TIME_SECONDS
        else:
            self._break_time = max(config.MIN_BREAK_TIME_SECONDS, break_time_seconds)

        self._break_time_counter_seconds = self._break_time
        self.current_session_start_time_epoch = time.time() # Start time of the current window activity
        self._break_timer_absolute_start_epoch = time.time() # When the overall break timer period started

        self.previous_window_exe = None # To display in UI
        self.thread = None
        app_logger.info("WindowTracker initialized.")

    @property
    def break_time_counter_display(self): # Renamed to avoid conflict and clarify purpose
        time_frame = int(self._break_time_counter_seconds)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    @property
    def is_running(self):
        return self.running
    
    # Setter for break_time_counter_seconds is not really needed as it's calculated
    
    @property
    def break_time_setting_display(self): # Renamed
        time_frame = int(self._break_time)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    @break_time_setting_display.setter # Renamed, and setter now acts on _break_time
    def break_time_setting_display(self, total_seconds):
        if isinstance(total_seconds, int) and total_seconds >= config.MIN_BREAK_TIME_SECONDS:
            self._break_time = total_seconds
            app_logger.info(f"Break time setting updated to {total_seconds} seconds.")
        else:
            messagebox.showerror("Invalid Break Time", f"Break time must be an integer and at least {config.MIN_BREAK_TIME_SECONDS // 60} minutes.")
            self._break_time = config.DEFAULT_BREAK_TIME_SECONDS # Reset to default
            app_logger.warning(f"Invalid break time set. Reset to default {self._break_time} seconds.")
        # Reset current break countdown when setting changes
        self._break_timer_absolute_start_epoch = time.time()
        self._break_time_counter_seconds = self._break_time


    # Removed break_timer_start property as it's an epoch time, not for display

    def reset_break_timer_countdown(self): # Renamed for clarity
        self._break_timer_absolute_start_epoch = time.time()
        self._break_time_counter_seconds = self._break_time # Reset countdown
        app_logger.info("Break timer countdown reset.")


    def get_active_window_info(self): # Renamed for clarity
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0: # No foreground window
                return "Idle", "No Active Window"
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0: # Should not happen if hwnd is valid
                 return "UnknownProcess", "Unknown Window (PID 0)"
            process = psutil.Process(pid)
            app_name = process.name().replace(".exe", "")
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title: # If empty title, use app_name
                window_title = app_name 
            return app_name, window_title
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # These are expected if the window closes quickly or belongs to a protected process
            app_logger.debug(f"Psutil process error (NoSuchProcess/AccessDenied/Zombie) for PID (likely transient).", exc_info=False) # Log as debug, not error
            return "Unknown", "Error Accessing Window"
        except Exception as e:
            app_logger.error(f"Unexpected error in get_active_window_info: {e}", exc_info=True)
            return "Unknown", "Error Fetching Window"
    
    def should_take_break(self): # Renamed for clarity
        return self._break_time_counter_seconds < 0

    def track_windows(self):
        app_logger.info("Window tracking thread started.")
        # print_app_debug_flag = True # CORRECTED: Replaced with logger

        while self.running:
            current_time_epoch = time.time()
            self._break_time_counter_seconds = self._break_time - (current_time_epoch - self._break_timer_absolute_start_epoch)

            # if self.should_take_break(): # Break check handled by UI now via property
            #     self._break_timer_absolute_start_epoch = current_time_epoch # Reset timer after break indication

            current_exe, current_title = self.get_active_window_info()

            if current_exe and current_exe != self.active_window_exe:
                app_logger.debug(f"Window changed from '{self.active_window_exe}' to '{current_exe}'.")
                # Log activity for the PREVIOUS window before updating
                if self.active_window_exe: # Ensure there was a previous active window
                    self.log_activity_for_current_window(self.active_window_title) # Use the stored title
                
                # Update to the new window
                self.previous_window_exe = self.active_window_exe
                self.active_window_exe = current_exe
                self.active_window_title = current_title
                self.current_session_start_time_epoch = current_time_epoch # Reset start time for new window
                self.current_session_total_time_seconds = 0 # Reset time for new window session

                if current_exe not in self.category_map and current_exe != "Unknown" and current_exe != "Idle":
                    app_logger.info(f"Program '{current_exe}' not found in category map. Requesting user input.")
                    # Category is obtained via logger_instance method, which updates its own map
                    category = self.logger_instance.get_category(current_exe)
                    # self.category_map[current_exe] = category # No need, get_category handles this
                    app_logger.info(f"Program '{current_exe}' assigned to category '{category}'.")
            
            # Update total time for the currently active window (even if it hasn't changed)
            if self.active_window_exe: # if there is an active window
                 self.current_session_total_time_seconds = current_time_epoch - self.current_session_start_time_epoch

            # CORRECTED: Removed the old print_app logic, rely on logger and UI updates
            # else:
            #     if print_app_debug_flag and self.previous_window_exe:
            #         app_logger.debug(f"Still in App: {self.active_window_exe} (Prev: {self.previous_window_exe} | Time in prev: {self.current_session_total_time_seconds:.2f}s)")
            #         print_app_debug_flag = False
            
            time.sleep(1) # Check every second

        # Loop finished (self.running is False)
        # Log the very final window activity before exiting thread
        if self.active_window_exe:
            self.log_activity_for_current_window(self.active_window_title)
        
        self.update_user_category_data() # Save category map on exit
        app_logger.info("Window tracking thread stopped.")


    def log_activity_for_current_window(self, window_title_to_log):
        # This method is called when a window *changes* or when tracking stops.
        # It logs the activity for the window that was *just active*.
        if self.active_window_exe: # Check if there's an exe name to log
            # Ensure total time for the session is up-to-date before logging
            end_time_epoch = time.time() # current time is end time for this activity
            # If current_session_start_time_epoch was just set (e.g. first ever window), ensure total time is calculated from it
            # If it's an ongoing session, self.current_session_total_time_seconds already reflects duration till last second.
            # The most accurate duration is end_time_epoch - self.current_session_start_time_epoch
            duration_seconds = end_time_epoch - self.current_session_start_time_epoch

            if duration_seconds < 0.5: # Avoid logging extremely short (<0.5s) interactions
                app_logger.debug(f"Skipping log for '{self.active_window_exe}': duration too short ({duration_seconds:.2f}s).")
                return

            app_logger.debug(f"Logging final activity for '{self.active_window_exe}', Title: '{window_title_to_log.split('\\')}', Start: {self.current_session_start_time_epoch}, End: {end_time_epoch}, Duration: {duration_seconds:.2f}s")
            self.log_activity(self.active_window_exe, window_title_to_log, 
                              self.current_session_start_time_epoch, end_time_epoch, duration_seconds)
            # self.current_session_start_time_epoch will be reset when the new window becomes active.
            # self.current_session_total_time_seconds will also be reset.

    def start_tracking(self):
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self.track_windows, daemon=True)
            self.thread.start()
            app_logger.info("start_tracking called, new tracking thread initiated.")
        else:
            app_logger.warning("start_tracking called, but a tracking thread is already running.")


    def stop_tracking(self):
        app_logger.info("stop_tracking called.")
        self.running = False
        if self.thread and self.thread.is_alive():
            app_logger.info("Attempting to join tracking thread...")
            self.thread.join(timeout=5) # Wait for up to 5 seconds for the thread to finish
            if self.thread.is_alive():
                app_logger.warning("Tracking thread did not finish in time.")
            else:
                app_logger.info("Tracking thread successfully joined.")
        self.thread = None


    def update_user_category_data(self):
        # This now directly calls the logger's method to save its category_map
        # The category_map in this tracker is a reference to logger_instance.category_map
        try:
            self.logger_instance.save_dict_to_txt(str(config.USER_PROGRAMS_FILE_PATH))
            app_logger.info("User category data update requested (via logger instance).")
        except Exception as e:
            app_logger.error(f"Failed to trigger save for user category data: {e}", exc_info=True)