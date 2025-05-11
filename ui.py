import tkinter as tk
from tkinter import ttk, messagebox,filedialog
import time
import os # For checking icon file existence

# ADDED:
import config
from app_logger import app_logger
from datetime import date as datetime_date 

class TimeTrackerUI:
    def __init__(self, root, tracker, graph_display, theme, logger_instance): # CORRECTED: logger_instance
        self.root = root
        self.tracker = tracker
        self.graph_display = graph_display
        self.theme = theme
        self.logger = logger_instance # Use the passed logger object consistently
        self.setup_ui()
        app_logger.info("TimeTrackerUI initialized.")

#   region initiate GUI

    def setup_ui(self):
        self.root.configure(bg=self.theme.windowBg())
        self.root.title("Time Tracker")
        self.root.minsize(width=450, height=400) # Slightly increased minsize

        # CORRECTED: Use configured icon path and check existence
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

        self.categories_listbox = tk.Listbox(self.root, height=6, width=50, bg=self.theme.buttonBg(), fg="white", font=("Consolas", 10))
        self.categories_listbox.pack(pady=(0,5))
        self.update_category_list() # Initial population

        # categories_discription = tk.Label(self.root, text="Category entry: name (count) | percentage", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "8"))
        # categories_discription.pack() # Removed, description integrated into label above

        self.current_app_time_label = tk.Label(self.root, text="Current App Time: 00:00:00", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "11"))
        self.current_app_time_label.pack(pady=2)

        self.current_window_label = tk.Label(self.root, text="Active Window: None", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "11", "bold"))
        self.current_window_label.pack(pady=2)
        
        self.previous_window_label = tk.Label(self.root, text="Previous Window: None", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "9"))
        self.previous_window_label.pack(pady=2)


        def change_break_time_window():
            app_logger.debug("Change break time window opened.")
            top_change_time_window = tk.Toplevel(self.root, bg=self.theme.windowBg())
            top_change_time_window.title("Set Break Interval")
            top_change_time_window.transient(self.root) # Associate with main window
            top_change_time_window.grab_set() # Modal
            top_change_time_window.attributes("-topmost", True)

            current_break_setting_minutes = self.tracker._break_time // 60

            tk.Label(top_change_time_window, text=f"Current interval: {current_break_setting_minutes} minutes.\nEnter new interval in minutes (min {config.MIN_BREAK_TIME_SECONDS // 60}):", 
                     bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10")).pack(padx=10, pady=10)
            
            time_window_entry_var = tk.StringVar(value=str(current_break_setting_minutes))
            time_window_entry = ttk.Entry(top_change_time_window, textvariable=time_window_entry_var, width=10)
            time_window_entry.pack(padx=10,pady=5)
            time_window_entry.focus_set()

            def submit_new_time():
                try:
                    new_time_minutes = int(time_window_entry_var.get())
                    new_time_seconds = new_time_minutes * 60
                    self.tracker.break_time_setting_display = new_time_seconds # Use the property setter
                    self.time_for_break_label.config(text=f"Break Interval: {self.tracker.break_time_setting_display}")
                    app_logger.info(f"Break time interval changed to {new_time_minutes} minutes.")
                    top_change_time_window.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid number for minutes.", parent=top_change_time_window)
                    app_logger.warning("Invalid input for break time minutes.")
                # Property setter in tracker already shows error for too low values

            entry_button = tk.Button(top_change_time_window, text="Set Interval", command=submit_new_time, 
                                     bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                     activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
            entry_button.pack(pady=10)
            time_window_entry.bind("<Return>", lambda event: submit_new_time())
            top_change_time_window.protocol("WM_DELETE_WINDOW", top_change_time_window.destroy)


        def reset_current_break_countdown():
            self.tracker.reset_break_timer_countdown()
            app_logger.info("Break countdown timer reset via UI button.")

        break_timer_frame = tk.Frame(self.root, bg=self.theme.windowBg())
        break_timer_frame.pack(pady=(10, 5))

        change_break_time_button = tk.Button(break_timer_frame, text="Set Break Interval", command=change_break_time_window, 
                                             bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10"),
                                             activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        change_break_time_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.time_for_break_label = tk.Label(break_timer_frame, text=f"Break Interval: {self.tracker.break_time_setting_display}", 
                                             bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10"))
        self.time_for_break_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        reset_countdown_button = tk.Button(break_timer_frame, text="Reset Break Countdown", command=reset_current_break_countdown, 
                                           bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10"),
                                           activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        reset_countdown_button.grid(row=1, column=0, padx=5, pady=5)

        self.break_countdown_label = tk.Label(break_timer_frame, text=f"Time Until Next Break: {self.tracker.break_time_counter_display}", 
                                             bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10", "bold"))
        self.break_countdown_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")


        button_frame = tk.Frame(self.root, bg=self.theme.windowBg()) # Changed to windowBg for consistency
        button_frame.pack(pady=(10, 5))

        graph_button = tk.Button(button_frame, text="Show Usage Graph", command=self.show_graph_ui, # Renamed method
                                 bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        graph_button.pack(pady=5) # Added padding

        # Add Export Report button
        export_report_button = tk.Button(button_frame, text="Export Activity Report", command=self.open_export_report_dialog,
                                         bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                         activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        export_report_button.pack(pady=5, after=graph_button) # Place it after the graph button


        close_button = tk.Button(self.root, text="Close Time Tracker", command=self.close_program, 
                                 bg=self.theme.closeButtonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.closeActiveButtonBg(), activeforeground="white", borderwidth=2)
        close_button.pack(pady=(5, 10))

        self.root.deiconify() # Show after setup
        self.update_ui_elements() # Start UI update loop
        app_logger.debug("UI setup complete.")

# ADDED: Method to open the export report dialog
    def open_export_report_dialog(self):
        app_logger.debug("Export report dialog opened.")
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Report Options")
        dialog.configure(bg=self.theme.windowBg())
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.attributes("-topmost", True)
        dialog.geometry("400x300") # Adjust size as needed

        # --- Radio buttons for report type ---
        report_type_var = tk.StringVar(value="all") # Default to "all"
        
        tk.Label(dialog, text="Report Type:", bg=self.theme.windowBg(), fg="white", font=("Helvetica", 11, "bold")).pack(pady=(10,0))
        
        all_data_rb = tk.Radiobutton(dialog, text="All Data", variable=report_type_var, value="all",
                                     bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg(), 
                                     activebackground=self.theme.windowBg(), activeforeground="white",
                                     command=lambda: toggle_date_fields("disabled"))
        all_data_rb.pack(anchor="w", padx=20)
        
        date_range_rb = tk.Radiobutton(dialog, text="Specific Date Range", variable=report_type_var, value="range",
                                       bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg(),
                                       activebackground=self.theme.windowBg(), activeforeground="white",
                                       command=lambda: toggle_date_fields("normal"))
        date_range_rb.pack(anchor="w", padx=20)

        # --- Date Entry Fields (initially disabled) ---
        date_frame = tk.Frame(dialog, bg=self.theme.windowBg())
        date_frame.pack(pady=5, padx=20, fill="x")

        tk.Label(date_frame, text="Start Date (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=0, column=0, sticky="w", pady=2)
        start_date_entry = tk.Entry(date_frame, width=15, state="disabled", bg=self.theme.buttonBg(), fg="white", disabledbackground=self.theme.activeButtonBg())
        start_date_entry.grid(row=0, column=1, pady=2)
        # Pre-fill with a sensible default if you like, e.g., start of current month
        start_date_entry.insert(0, datetime_date.today().replace(day=1).strftime('%d/%m/%Y'))


        tk.Label(date_frame, text="End Date (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=1, column=0, sticky="w", pady=2)
        end_date_entry = tk.Entry(date_frame, width=15, state="disabled", bg=self.theme.buttonBg(), fg="white", disabledbackground=self.theme.activeButtonBg())
        end_date_entry.grid(row=1, column=1, pady=2)
        # Pre-fill with today's date
        end_date_entry.insert(0, datetime_date.today().strftime('%d/%m/%Y'))


        def toggle_date_fields(new_state):
            start_date_entry.config(state=new_state)
            end_date_entry.config(state=new_state)

        # --- Export Button ---
        def do_export():
            export_type = report_type_var.get()
            start_date = None
            end_date = None
            
            if export_type == "range":
                start_date = start_date_entry.get()
                end_date = end_date_entry.get()
                if not start_date or not end_date:
                    messagebox.showwarning("Missing Dates", "Please enter both start and end dates for a ranged report.", parent=dialog)
                    return
            
            # Call the logger's export method
            self.logger.export_activity_report(export_type, start_date, end_date)
            # Optionally close the dialog after export attempt, or let user close it.
            dialog.destroy() 

        export_button = tk.Button(dialog, text="Generate and Export Report", 
                                  command=do_export,
                                  bg=self.theme.buttonBg(), fg="white", font=("Helvetica", 10, "bold"),
                                  activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        export_button.pack(pady=20)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
#   region update GUI

    def update_category_list(self):
        self.categories_listbox.delete(0, tk.END)
        if not self.logger.df.empty and 'category' in self.logger.df.columns:
            category_counts = self.logger.df['category'].value_counts()
            total_log_entries = len(self.logger.df) # Use total entries for percentage
            
            # Sort categories by count for display
            sorted_categories = category_counts.index.tolist()
            if "Misc" in sorted_categories: # Ensure Misc is last if it exists
                sorted_categories.remove("Misc")
                sorted_categories.append("Misc")

            for category in sorted_categories:
                count = category_counts[category]
                percentage = (count / total_log_entries) * 100 if total_log_entries > 0 else 0
                self.categories_listbox.insert(tk.END, f"{category:<20} ({count:>4} entries | {percentage:>5.1f}%)")
        else:
            self.categories_listbox.insert(tk.END, "No activity logged yet.")
        app_logger.debug("Category listbox updated.")


    _break_message_shown_this_cycle = False # Class variable to track if break message shown for current cycle

    def update_ui_elements(self): # Renamed from update_running_time
        # Update current application time
        current_app_time_seconds = self.tracker.current_session_total_time_seconds
        h, rem = divmod(int(current_app_time_seconds), 3600)
        m, s = divmod(rem, 60)
        self.current_app_time_label.config(text=f"Current App Time: {h:02}:{m:02}:{s:02}")

        # Update active and previous window labels
        active_exe = self.tracker.active_window_exe or "None"
        active_title = self.tracker.active_window_title or ""
        # Truncate long titles for display
        display_title = active_title if len(active_title) < 70 else active_title[:67] + "..."
        self.current_window_label.config(text=f"Active: {active_exe} - {display_title}")
        
        prev_exe = self.tracker.previous_window_exe or "None"
        self.previous_window_label.config(text=f"Previous: {prev_exe}")
        
        # Update break timer display
        self.break_countdown_label.config(text=f"Time Until Next Break: {self.tracker.break_time_counter_display}")

        # Check for break time
        if self.tracker.should_take_break():
            if not TimeTrackerUI._break_message_shown_this_cycle:
                app_logger.info("Break time reached. Showing notification.")
                messagebox.showinfo("Break Time!", "It's time to take a break.")
                TimeTrackerUI._break_message_shown_this_cycle = True # Mark as shown
                self.tracker.reset_break_timer_countdown() # Automatically reset after showing message
                self.update_category_list() # Refresh categories listbox, might have new data after a long session
        else:
            TimeTrackerUI._break_message_shown_this_cycle = False # Reset flag if not break time
        try:
            # Schedule next update
            if self.tracker.is_running:
                self.root.after(1000, self.update_ui_elements)
            # app_logger.debug("UI elements updated.") # Too frequent for debug log
        except Exception as e:
            app_logger.error(f"Error updating UI elements: {e}", exc_info=True)
            messagebox.showerror("UI Update Error", f"An error occurred while updating the UI: {e}", parent=self.root)

#   region Buttons

    def show_graph_ui(self): # Renamed from get_graph
        app_logger.info("Show graph button clicked.")
        # Ensure logger's DataFrame is up-to-date before showing graph
        # self.logger.save_log_to_csv() # This might be too aggressive, data is saved periodically
        
        if self.graph_display.is_open:
            app_logger.debug("Graph window already open. Attempting to close old one.")
            # Find and destroy existing graph window if any (more robustly)
            for w in self.root.winfo_children():
                if isinstance(w, tk.Toplevel) and w.title() == "Category Percentage Comparison": # Check title
                    w.destroy()
                    self.graph_display.is_open = False
                    app_logger.debug("Closed existing graph window.")
                    break
        
        # Always load fresh data from logger's current df for the graph
        current_log_df = self.logger.df 
        if current_log_df is not None and not current_log_df.empty:
            self.graph_display.show_graph(current_log_df)
        else:
            messagebox.showinfo("No Data", "No data has been logged yet to display a graph.", parent=self.root)
            app_logger.warning("Graph display requested but no data in logger.df.")


    def close_program(self):
        app_logger.info("Close program sequence initiated by UI.")
        self.tracker.stop_tracking() # This will log final activity and save category map
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to close Time Tracker?", parent=self.root):
            app_logger.info("User confirmed exit.")
            #self.tracker.stop_tracking() # This will log final activity and save category map

            # Log final data from self.logger.log (if any pending) one last time
            if self.logger.log: # If there are unsaved entries in the list
                 app_logger.info("Performing final save of in-memory log entries before exit.")
                 self.logger.save_log_to_csv()

            if self.graph_display.is_open:
                app_logger.debug("Closing open graph window during program exit.")
                for w in self.root.winfo_children():
                    if isinstance(w, tk.Toplevel) and w.title() == "Category Percentage Comparison":
                        w.destroy()
                        self.graph_display.is_open = False
                        break
            
            app_logger.info("Destroying main application window.")
            time.sleep(0.5)
            self.root.destroy()
            self.root.quit() # destroy() usually handles this for Tk object.
        else:
            app_logger.info("User cancelled exit.")
            self.tracker.start_tracking() # Restart tracking if exit was cancelled