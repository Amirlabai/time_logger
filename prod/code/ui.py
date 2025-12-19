# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import os # For checking icon file existence

import config # <<< Make sure this is imported
from app_logger import app_logger
from datetime import date as datetime_date # For pre-filling dates in export dialog

class TimeTrackerUI:
    def __init__(self, root, tracker, graph_display, theme, logger_instance):
        self.root = root
        self.tracker = tracker
        self.graph_display = graph_display # GraphDisplay will use logger_instance to get data
        self.theme = theme
        self.logger = logger_instance # This is the SQLite-backed Logger instance
        self.run_image = None
        self.pause_image = None
        
        self.setup_ui()
        
        # Start queue processing for thread-safe GUI operations (after UI is set up)
        self._process_gui_queue()
        
        app_logger.info("TimeTrackerUI initialized (SQLite mode).")

    def setup_ui(self):
        self.root.configure(bg=self.theme.windowBg())
        self.root.title("Time Tracker")
        self.root.minsize(width=450, height=400)

        timer_icon_path_str = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str):
            try:
                self.root.iconbitmap(timer_icon_path_str)
            except tk.TclError as e:
                app_logger.warning(f"Failed to set timer icon ({timer_icon_path_str}): {e}. Using default.")
        else:
            app_logger.warning(f"Timer icon not found at {timer_icon_path_str}. Using default.")
        
        self.root.withdraw() # Hide until setup is complete

        categories_label = tk.Label(self.root, text="Categories Tracked (Activity Count | % of Entries):", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold"))
        categories_label.pack(pady=(10,2))

        self.categories_listbox = tk.Listbox(self.root, height=6, width=60, bg=self.theme.buttonBg(), fg="white", font=("Consolas", 10)) # Increased width slightly
        self.categories_listbox.pack(pady=(0,5))
        self.update_category_list() # Initial population

        edit_categories_button = tk.Button(
            self.root,
            text="Edit Program Categories",
            command=lambda: self.logger.open_edit_program_categories_window(self.root), # This method in Logger is now SQLite-aware
            bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
            activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2
        )
        edit_categories_button.pack(pady=(5,5))

        self.current_app_time_label = tk.Label(self.root, text="Current App Time: 00:00:00", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "11"))
        self.current_app_time_label.pack(pady=2)

        self.current_window_label = tk.Label(self.root, text="Active Window: None", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "11", "bold"), wraplength=430, justify="center")
        self.current_window_label.pack(pady=2)
        
        self.previous_window_label = tk.Label(self.root, text="Previous Window: None", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "9"))
        self.previous_window_label.pack(pady=2)

        def change_break_time_window():
            app_logger.debug("Change break time window opened.")
            top_change_time_window = tk.Toplevel(self.root, bg=self.theme.windowBg())
            top_change_time_window.title("Set Break Interval")
            top_change_time_window.transient(self.root) 
            top_change_time_window.grab_set() 
            top_change_time_window.attributes("-topmost", True)
            
            # <<< START ICON SETUP for change_break_time_window >>>
            timer_icon_path_str_dialog = str(config.TIMER_ICON_PATH)
            if os.path.exists(timer_icon_path_str_dialog):
                try:
                    top_change_time_window.iconbitmap(timer_icon_path_str_dialog)
                except tk.TclError as e:
                    app_logger.warning(f"Failed to set timer icon for Set Break Interval dialog: {e}")
            else:
                app_logger.warning(f"Timer icon not found for Set Break Interval dialog: {timer_icon_path_str_dialog}")
            # <<< END ICON SETUP for change_break_time_window >>>

            current_break_setting_minutes = self.tracker._break_time // 60
            tk.Label(top_change_time_window, text=f"Current interval: {current_break_setting_minutes} mins.\nEnter new interval (min {config.MIN_BREAK_TIME_SECONDS // 60}):", 
                     bg=self.theme.windowBg(), fg="white").pack(padx=10, pady=10)
            time_var = tk.StringVar(value=str(current_break_setting_minutes))
            entry = ttk.Entry(top_change_time_window, textvariable=time_var, width=10)
            entry.pack(pady=5); entry.focus_set()
            def submit():
                try:
                    new_min = int(time_var.get())
                    self.tracker.break_time_setting_display = new_min * 60
                    self.time_for_break_label.config(text=f"Break Interval: {self.tracker.break_time_setting_display}")
                    top_change_time_window.destroy()
                except ValueError: messagebox.showerror("Invalid", "Enter numbers only.", parent=top_change_time_window)
            btn = tk.Button(top_change_time_window, text="Set", command=submit, bg=self.theme.buttonBg(), fg="white")
            btn.pack(pady=10)
            entry.bind("<Return>", lambda e: submit())


        def reset_current_break_countdown():
            self.tracker.reset_break_timer_countdown()
            app_logger.info("Break countdown timer reset via UI button.")

        break_timer_frame = tk.Frame(self.root, bg=self.theme.windowBg())
        break_timer_frame.pack(pady=(10, 5), expand=True)

        change_break_time_button = tk.Button(break_timer_frame, text="Set Break Interval", command=change_break_time_window, bg=self.theme.buttonBg(), fg="white")
        change_break_time_button.grid(row=0, column=0, padx=5, pady=5)
        self.time_for_break_label = tk.Label(break_timer_frame, text=f"Break Interval: {self.tracker.break_time_setting_display}", bg=self.theme.windowBg(), fg="white")
        self.time_for_break_label.grid(row=0, column=1, padx=5, pady=5)
        reset_countdown_button = tk.Button(break_timer_frame, text="Reset Countdown", command=reset_current_break_countdown, bg=self.theme.buttonBg(), fg="white")
        reset_countdown_button.grid(row=1, column=0, padx=5, pady=5)
        self.break_countdown_label = tk.Label(break_timer_frame, text=f"Time Until Next Break: {self.tracker.break_time_counter_display}", bg=self.theme.windowBg(), fg="white")
        self.break_countdown_label.grid(row=1, column=1, padx=5, pady=5)


        run_image_path_str = str(config.RUN_IMAGE_PATH)
        if os.path.exists(run_image_path_str): self.run_image = tk.PhotoImage(file=run_image_path_str)
        pause_image_path_str = str(config.PAUSE_IMAGE_PATH)
        if os.path.exists(pause_image_path_str): self.pause_image = tk.PhotoImage(file=pause_image_path_str)

        self.run_countdown_button = tk.Button(break_timer_frame, image=self.run_image if not self.tracker.is_running_break_time else self.pause_image, 
                                             width=30, height=30, bg=self.theme.buttonBg(), command=self.flag_breaktime)
        if self.run_image: self.run_countdown_button.image = self.run_image 
        self.run_countdown_button.grid(row=0, rowspan=2, column=2, padx=5, pady=5)


        button_frame = tk.Frame(self.root, bg=self.theme.windowBg())
        button_frame.pack(pady=(10, 5))

        graph_button = tk.Button(button_frame, text="Show Usage Graph", command=self.show_graph_ui,
                                 bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        graph_button.pack(pady=5)

        export_report_button = tk.Button(button_frame, text="Export Activity Report", command=self.open_export_report_dialog,
                                         bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                         activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        export_report_button.pack(pady=5, after=graph_button)

        close_button = tk.Button(self.root, text="Close Time Tracker", command=self.close_program, 
                                 bg=self.theme.closeButtonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.closeActiveButtonBg(), activeforeground="white", borderwidth=2)
        close_button.pack(pady=(5, 10))

        self._break_message_shown_this_cycle = False  # Instance variable, not class variable
        self.root.deiconify()
        self.update_ui_elements()
        app_logger.debug("UI setup complete (SQLite mode).")

    def open_export_report_dialog(self):
        app_logger.debug("Export report dialog opened.")
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Report Options")
        dialog.configure(bg=self.theme.windowBg())
        dialog.transient(self.root); dialog.grab_set(); dialog.attributes("-topmost", True)
        dialog.geometry("400x300") # You might want to adjust this based on content
        
        # <<< START ICON SETUP for export dialog >>>
        # Using TIMER_ICON_PATH as a generic icon for dialogs, adjust if you have a specific one for reports
        timer_icon_path_str_dialog = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str_dialog):
            try:
                dialog.iconbitmap(timer_icon_path_str_dialog)
            except tk.TclError as e:
                app_logger.warning(f"Failed to set timer icon for export dialog: {e}")
        else:
            app_logger.warning(f"Timer icon not found for export dialog: {timer_icon_path_str_dialog}")
        # <<< END ICON SETUP for export dialog >>>
        
        report_type_var = tk.StringVar(value="all")
        tk.Label(dialog, text="Report Type:", bg=self.theme.windowBg(), fg="white").pack(pady=(10,0))
        
        # Create date_frame first
        date_frame = tk.Frame(dialog, bg=self.theme.windowBg())
        
        # Now create Entry widgets with date_frame as their parent
        start_date_entry = tk.Entry(date_frame, width=15, state="disabled", bg=self.theme.buttonBg(), fg="white")
        end_date_entry = tk.Entry(date_frame, width=15, state="disabled", bg=self.theme.buttonBg(), fg="white")

        def toggle_date_fields(state):
            start_date_entry.config(state=state)
            end_date_entry.config(state=state)

        tk.Radiobutton(dialog, text="All Data", variable=report_type_var, value="all", command=lambda: toggle_date_fields("disabled"), bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg()).pack(anchor="w", padx=20)
        tk.Radiobutton(dialog, text="Date Range", variable=report_type_var, value="range", command=lambda: toggle_date_fields("normal"), bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg()).pack(anchor="w", padx=20)
        
        date_frame.pack(pady=5, padx=20, fill="x") # Pack the date_frame into the dialog

        # Grid widgets within date_frame
        tk.Label(date_frame, text="Start (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=0, column=0, sticky="w", padx=(0,5))
        start_date_entry.grid(row=0, column=1, pady=2) 
        start_date_entry.insert(0, datetime_date.today().replace(day=1).strftime('%d/%m/%Y'))
        
        tk.Label(date_frame, text="End (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=1, column=0, sticky="w", padx=(0,5))
        end_date_entry.grid(row=1, column=1, pady=2)
        end_date_entry.insert(0, datetime_date.today().strftime('%d/%m/%Y'))

        # Ensure date_frame columns are configured if needed for alignment
        date_frame.columnconfigure(0, weight=0) # Label column
        date_frame.columnconfigure(1, weight=1) # Entry column

        def do_export():
            export_type = report_type_var.get()
            s_date, e_date = None, None
            if export_type == "range":
                s_date, e_date = start_date_entry.get(), end_date_entry.get()
                if not (s_date and e_date):
                    messagebox.showwarning("Missing Dates", "Please provide start and end dates.", parent=dialog)
                    return
            self.logger.export_activity_report(export_type, s_date, e_date)
            dialog.destroy()

        tk.Button(dialog, text="Generate and Export", command=do_export, bg=self.theme.buttonBg(), fg="white").pack(pady=20)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def update_category_list(self):
        self.categories_listbox.delete(0, tk.END)
        all_log_data_df = self.logger.get_all_logged_data() 

        if not all_log_data_df.empty and 'category' in all_log_data_df.columns:
            category_counts = all_log_data_df['category'].value_counts()
            total_log_entries = len(all_log_data_df)
            
            sorted_categories = category_counts.index.tolist() 

            for category_name in sorted_categories:
                count = category_counts[category_name]
                percentage = (count / total_log_entries) * 100 if total_log_entries > 0 else 0
                self.categories_listbox.insert(tk.END, f"{category_name:<25} ({count:>5} entries | {percentage:>6.1f}%)")
        else:
            self.categories_listbox.insert(tk.END, "No activity logged yet or no categories found.")
        app_logger.debug("Category listbox updated from DB data.")

    def update_ui_elements(self):
        current_app_time_seconds = self.tracker.current_session_total_time_seconds
        h, rem = divmod(int(current_app_time_seconds), 3600)
        m, s = divmod(rem, 60)
        self.current_app_time_label.config(text=f"Current App Time: {h:02}:{m:02}:{s:02}")

        active_exe = self.tracker.active_window_exe or "None"
        active_title = self.tracker.active_window_title or ""
        display_title = active_title if len(active_title) < 60 else active_title[:57] + "..." 
        self.current_window_label.config(text=f"Active: {active_exe} - {display_title}")
        
        prev_exe = self.tracker.previous_window_exe or "None"
        self.previous_window_label.config(text=f"Previous: {prev_exe}")
        
        self.break_countdown_label.config(text=f"Time Until Next Break: {self.tracker.break_time_counter_display}")

        if self.tracker.should_take_break():
            if not self._break_message_shown_this_cycle:
                app_logger.info("Break time reached. Showing notification.")
                messagebox.showinfo("Break Time!", "It's time to take a break.")
                self._break_message_shown_this_cycle = True
                self.tracker.reset_break_timer_countdown()
                self.flag_breaktime()

                self.update_category_list() 
        else:
            self._break_message_shown_this_cycle = False
        
        if self.tracker.is_running: 
            self.root.after(1000, self.update_ui_elements)
    
    def _process_gui_queue(self):
        """
        Process GUI requests from the background tracking thread.
        This method polls the queue and handles category requests on the main thread.
        """
        try:
            while not self.tracker.gui_queue.empty():
                try:
                    request_type, data = self.tracker.gui_queue.get_nowait()
                    
                    if request_type == "request_category":
                        program_name = data
                        app_logger.debug(f"Processing category request for '{program_name}' on main thread.")
                        
                        # Get category using GUI (this runs on main thread)
                        category = self.logger.get_category(program_name, parent_root=self.root)
                        
                        # Notify the background thread of the result
                        if program_name in self.tracker._pending_category_requests:
                            event, result_dict = self.tracker._pending_category_requests[program_name]
                            result_dict["category"] = category
                            event.set()  # Signal that result is ready
                    else:
                        app_logger.warning(f"Unknown GUI queue request type: {request_type}")
                        
                except Exception as e:
                    app_logger.error(f"Error processing GUI queue request: {e}", exc_info=True)
        except Exception as e:
            app_logger.error(f"Error in _process_gui_queue: {e}", exc_info=True)
        
        # Schedule next check (poll every 100ms)
        if self.tracker.is_running:
            self.root.after(100, self._process_gui_queue)

    def flag_breaktime(self):
        if self.tracker.is_running_break_time:
            self.tracker.is_running_break_time = False
            if self.run_image: self.run_countdown_button.config(image=self.run_image)
        else:
            self.tracker.is_running_break_time = True
            if self.pause_image: self.run_countdown_button.config(image=self.pause_image)

    def show_graph_ui(self):
        app_logger.info("Show graph button clicked.")
        
        if self.graph_display.is_open:
            app_logger.debug("Graph window already open. Attempting to close old one.")
            for w in self.root.winfo_children(): 
                if isinstance(w, tk.Toplevel) and w.title() == self.graph_display.graph_window_title: 
                    w.destroy()
                    self.graph_display.is_open = False 
                    break
        
        self.graph_display.show_graph() 

    def close_program(self):
        app_logger.info("Close program sequence initiated by UI.")
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to close Time Tracker?", parent=self.root):
            app_logger.info("User confirmed exit.")
            self.tracker.stop_tracking()

            if self.graph_display.is_open: 
                app_logger.debug("Closing open graph window during program exit.")
                for w in self.root.winfo_children(): # More robust closing
                    if isinstance(w, tk.Toplevel) and w.title() == self.graph_display.graph_window_title:
                        w.destroy()
                        self.graph_display.is_open = False 
                        break

            app_logger.info("Destroying main application window.")
            self.root.quit()
        else:
            app_logger.info("User cancelled exit.")
            if not self.tracker.is_running:
                 self.tracker.start_tracking()