# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import os # For checking icon file existence
from datetime import datetime, timedelta # Ensure datetime is imported

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

        def flag_breaktime():
            if self.tracker.is_running_break_time:
                self.tracker.is_running_break_time = False
                if self.run_image: self.run_countdown_button.config(image=self.run_image)
            else:
                self.tracker.is_running_break_time = True
                if self.pause_image: self.run_countdown_button.config(image=self.pause_image)

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
                                             width=30, height=30, bg=self.theme.buttonBg(), command=flag_breaktime)
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

    def show_report_window(self):
        # This is a placeholder method.
        # It will be implemented in the next step.
        # app_logger.info("show_report_window called") # Comment out or remove placeholder log

        report_window = tk.Toplevel(self.root)
        report_window.title("Activity Report")
        report_window.configure(bg=self.theme.windowBg())
        report_window.transient(self.root)
        report_window.grab_set()
        report_window.geometry("800x600") # Adjusted size for more content

        # Icon for the report window
        timer_icon_path_str_dialog = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str_dialog):
            try:
                report_window.iconbitmap(timer_icon_path_str_dialog)
            except tk.TclError as e:
                app_logger.warning(f"Failed to set timer icon for report window: {e}")
        else:
            app_logger.warning(f"Timer icon not found for report window: {timer_icon_path_str_dialog}")

        # --- Data Storage ---
        self.current_raw_df = None # Stores raw data filtered by date
        self.current_display_df = None # Stores data prepared for display (raw or aggregated)
        self.report_view_mode = tk.StringVar(value="detailed") # 'detailed' or 'summary'

        # --- UI Frames ---
        top_frame = tk.Frame(report_window, bg=self.theme.windowBg())
        top_frame.pack(pady=10, padx=10, fill="x")

        tree_frame = tk.Frame(report_window, bg=self.theme.windowBg())
        tree_frame.pack(pady=5, padx=10, fill="both", expand=True)

        bottom_frame = tk.Frame(report_window, bg=self.theme.windowBg())
        bottom_frame.pack(pady=10, padx=10, fill="x")

        # --- Date Entry ---
        date_controls_frame = tk.Frame(top_frame, bg=self.theme.windowBg())
        date_controls_frame.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(date_controls_frame, text="Start Date (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=0, column=0, sticky="w", pady=2)
        start_date_var = tk.StringVar(value=datetime_date.today().replace(day=1).strftime('%d/%m/%Y'))
        start_date_entry = tk.Entry(date_controls_frame, textvariable=start_date_var, width=12, bg=self.theme.buttonBg(), fg="white")
        start_date_entry.grid(row=0, column=1, sticky="w", pady=2, padx=5)

        tk.Label(date_controls_frame, text="End Date (DD/MM/YYYY):", bg=self.theme.windowBg(), fg="white").grid(row=1, column=0, sticky="w", pady=2)
        end_date_var = tk.StringVar(value=datetime_date.today().strftime('%d/%m/%Y'))
        end_date_entry = tk.Entry(date_controls_frame, textvariable=end_date_var, width=12, bg=self.theme.buttonBg(), fg="white")
        end_date_entry.grid(row=1, column=1, sticky="w", pady=2, padx=5)

        # --- View Type Radio Buttons ---
        view_type_frame = tk.Frame(top_frame, bg=self.theme.windowBg())
        view_type_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(view_type_frame, text="View Type:", bg=self.theme.windowBg(), fg="white").pack(anchor="w")
        # report_view_type_var is now self.report_view_mode

        detailed_rb = tk.Radiobutton(view_type_frame, text="Detailed Log View", variable=self.report_view_mode, value="detailed",
                                     bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg(),
                                     activebackground=self.theme.windowBg(), activeforeground="white",
                                     command=self._on_view_mode_change) # Connect command
        detailed_rb.pack(anchor="w")

        summary_rb = tk.Radiobutton(view_type_frame, text="Summary View", variable=self.report_view_mode, value="summary",
                                   bg=self.theme.windowBg(), fg="white", selectcolor=self.theme.buttonBg(),
                                   activebackground=self.theme.windowBg(), activeforeground="white",
                                   command=self._on_view_mode_change) # Connect command
        summary_rb.pack(anchor="w")


        # --- Treeview ---
        # Columns will be set dynamically by _prepare_and_display_report_data
        self.report_treeview = ttk.Treeview(tree_frame, show="headings", selectmode="browse")
        self.report_treeview.column("#0", width=0, stretch=tk.NO) # Hide the default #0 column

        # Scrollbars for the treeview
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.report_treeview.yview)
        self.report_treeview.configure(yscrollcommand=tree_scrollbar_y.set)
        tree_scrollbar_y.pack(side="right", fill="y")

        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.report_treeview.xview)
        self.report_treeview.configure(xscrollcommand=tree_scrollbar_x.set)
        tree_scrollbar_x.pack(side="bottom", fill="x")

        self.report_treeview.pack(fill="both", expand=True)

        # --- Refresh Data Button ---
        def refresh_data_action():
            start_str = start_date_var.get()
            end_str = end_date_var.get()
            app_logger.info(f"Refreshing report data from {start_str} to {end_str}")
            # Basic validation (can be improved)
            try:
                datetime.strptime(start_str, '%d/%m/%Y')
                datetime.strptime(end_str, '%d/%m/%Y')
            except ValueError:
                messagebox.showerror("Invalid Date Format", "Please use DD/MM/YYYY format.", parent=report_window)
                return

            self.current_raw_df = self.logger.get_all_logged_data(start_date_str=start_str, end_date_str=end_str)
            self._prepare_and_display_report_data() # Process and display

        refresh_button = tk.Button(date_controls_frame, text="Refresh Data", command=refresh_data_action,
                                   bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10"),
                                   activebackground=self.theme.activeButtonBg(), activeforeground="white")
        refresh_button.grid(row=0, column=2, rowspan=2, padx=10, ipady=5)

        # --- Export to CSV Button ---
        def export_to_csv_action():
            if self.current_display_df is not None and not self.current_display_df.empty: # Use current_display_df
                app_logger.info(f"Export to CSV button clicked. Attempting to export {len(self.current_display_df)} rows.")
                self.logger.export_activity_report(data_for_report_df=self.current_display_df)
            else:
                messagebox.showwarning("No Data", "No data to export.", parent=report_window)
                app_logger.warning("Export to CSV: No data available in the report window to export.")

        export_button = tk.Button(bottom_frame, text="Export to CSV", command=export_to_csv_action,
                                  bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                  activebackground=self.theme.activeButtonBg(), activeforeground="white")
        export_button.pack(side=tk.RIGHT, padx=5)

        # --- Initial Data Load ---
        self.current_raw_df = self.logger.get_all_logged_data(start_date_str=start_date_var.get(), end_date_str=end_date_var.get())
        self._prepare_and_display_report_data() # Initial display

        report_window.protocol("WM_DELETE_WINDOW", report_window.destroy)

    def _on_view_mode_change(self):
        app_logger.info(f"View mode changed to: {self.report_view_mode.get()}")
        self._prepare_and_display_report_data()

    def _prepare_and_display_report_data(self):
        view_mode = self.report_view_mode.get()
        app_logger.debug(f"Preparing data for view mode: {view_mode}")

        # Clear existing treeview columns and content
        self.report_treeview.set_children('') # Clear rows
        for col in self.report_treeview["columns"]:
            self.report_treeview.heading(col, text="") # Clear headings to remove old ones
        self.report_treeview["columns"] = () # Remove all columns

        if self.current_raw_df is None or self.current_raw_df.empty:
            app_logger.debug("No raw data to display.")
            self.current_display_df = self.current_raw_df # Which is None or empty
            # Setup a single column to show "No data" message
            self.report_treeview['columns'] = ('Status',)
            self.report_treeview.heading('Status', text='Status')
            self.report_treeview.column('Status', width=780, anchor='center')
            self._populate_report_treeview(self.current_display_df) # Will show "No data"
            return

        if view_mode == "detailed":
            cols = ("Timestamp", "Application", "Window Title", "Category", "Duration (s)")
            col_widths = {"Timestamp": 150, "Application": 150, "Window Title": 250, "Category": 100, "Duration (s)": 80}

            # Use a copy to avoid modifying the raw DataFrame if direct pass-through
            # For detailed view, the structure is mostly the same, but ensure required columns are present
            # and 'duration_seconds' is what we have from logger.
            detailed_df = self.current_raw_df.copy()
            # Rename columns from DB names to Treeview display names for detailed view
            detailed_df.rename(columns={
                'timestamp': 'Timestamp', # Assuming 'timestamp' is how it comes from get_all_logged_data
                'app_name': 'Application',
                'window_title': 'Window Title',
                # 'category' is already 'Category' if it matches, or rename if different
                'duration_seconds': 'Duration (s)'
            }, inplace=True)
            # Ensure 'category' is named 'Category' if it's not already.
            if 'category' in detailed_df.columns and 'Category' not in detailed_df.columns:
                detailed_df.rename(columns={'category': 'Category'}, inplace=True)

            self.current_display_df = detailed_df

        elif view_mode == "summary":
            cols = ('Date', 'Category', 'Program Name', 'Total Time (min)')
            col_widths = {"Date": 100, "Category": 150, "Program Name": 200, "Total Time (min)": 100}

            # Perform aggregation
            # Convert duration_seconds to minutes for summary
            summary_df = self.current_raw_df.copy()
            summary_df['total_time_minutes'] = summary_df['duration_seconds'] / 60.0

            self.current_display_df = summary_df.groupby(
                ['date_text', 'category', 'app_name'], as_index=False
            )['total_time_minutes'].sum()

            # Rename columns for display in summary view
            self.current_display_df.rename(columns={
                'date_text': 'Date',
                'category': 'Category',
                'app_name': 'Program Name',
                'total_time_minutes': 'Total Time (min)'
            }, inplace=True)
            # Round the summed minutes
            self.current_display_df['Total Time (min)'] = self.current_display_df['Total Time (min)'].round(2)

        else:
            app_logger.error(f"Unknown view mode: {view_mode}")
            return

        # Configure Treeview columns
        self.report_treeview['columns'] = cols
        for col_name in cols:
            self.report_treeview.heading(col_name, text=col_name)
            self.report_treeview.column(col_name, width=col_widths.get(col_name, 150), anchor="w")

        self._populate_report_treeview(self.current_display_df)


    # --- Helper: Populate Treeview (modified for dynamic columns) ---
    def _populate_report_treeview(self, data_df):
        # Clear existing items (already done in _prepare_and_display_report_data, but good for safety)
        for item in self.report_treeview.get_children():
            self.report_treeview.delete(item)

        # self.current_display_df is already set by _prepare_and_display_report_data
        # This method now just focuses on populating with whatever data_df is given

        if data_df is not None and not data_df.empty:
            # The columns in data_df should now directly match the treeview columns set by _prepare_and_display_report_data
            tree_cols = self.report_treeview['columns']

            for index, row in data_df.iterrows():
                # Get values in the order of tree_cols
                tree_values = [row.get(col_name, "") for col_name in tree_cols]
                self.report_treeview.insert("", tk.END, values=tuple(tree_values))
            app_logger.debug(f"Report treeview populated with {len(data_df)} rows for view: {self.report_view_mode.get()}.")
        else:
            # If treeview has columns (e.g. 'Status' for no data), use them
            if self.report_treeview['columns'] and self.report_treeview['columns'][0] == 'Status':
                 self.report_treeview.insert("", tk.END, values=("No data for selected period or view.",))
            elif not self.report_treeview['columns']: # Should not happen if _prepare_and_display is correct
                self.report_treeview['columns'] = ('Status',)
                self.report_treeview.heading('Status', text='Status')
                self.report_treeview.column('Status', width=780, anchor='center')
                self.report_treeview.insert("", tk.END, values=("No data available.",))
            else: # Has other columns, but data is empty
                # Create a placeholder tuple matching the number of columns
                num_cols = len(self.report_treeview['columns'])
                placeholder_values = ["No data"] + [""] * (num_cols - 1) if num_cols > 0 else ["No data"]
                self.report_treeview.insert("", tk.END, values=tuple(placeholder_values))

            app_logger.debug(f"Report treeview: No data to display for view: {self.report_view_mode.get()}.")

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

    _break_message_shown_this_cycle = False 

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
            if not TimeTrackerUI._break_message_shown_this_cycle:
                app_logger.info("Break time reached. Showing notification.")
                messagebox.showinfo("Break Time!", "It's time to take a break.")
                TimeTrackerUI._break_message_shown_this_cycle = True
                self.tracker.reset_break_timer_countdown()
                self.update_category_list() 
        else:
            TimeTrackerUI._break_message_shown_this_cycle = False
        
        if self.tracker.is_running: 
            self.root.after(1000, self.update_ui_elements)


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
            time.sleep(2)
            self.root.destroy()
        else:
            app_logger.info("User cancelled exit.")
            if not self.tracker.is_running:
                 self.tracker.start_tracking()