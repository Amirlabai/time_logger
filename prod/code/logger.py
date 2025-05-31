import pandas as pd
import time
import os
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from themes import Theme
import datetime
import json
# ADDED:
import config
from app_logger import app_logger
from pathlib import Path
from tkinter import filedialog # ADDED for save dialog
from datetime import datetime # ADDED for date conversions

class Logger:
    def __init__(self, csv_file_path_str, theme): # CORRECTED: csv_file is now full path string
        self.csv_file_path = Path(csv_file_path_str) # Store as Path object
        self.theme = theme # Theme() is already instantiated in main, pass it directly.
        # self.category_map = self.load_dict_from_txt() # Load after df to ensure CATEGORIES are updated by df too
        self.df = self.load_existing_data() # This will also update CATEGORIES from existing log
        self.category_map = self.load_dict_from_txt(str(config.USER_PROGRAMS_FILE_PATH)) # Ensure this has all known categories
        self.program_vars = {} # Initialize here, will be used by the method
        
        # Initialize CATEGORIES from both existing log data and user_programs.txt
        self.CATEGORIES = set(self.category_map.values())
        if not self.df.empty and 'category' in self.df.columns:
            self.CATEGORIES.update(self.df['category'].unique())
        
        self.log = []
        app_logger.info(f"Logger initialized for {self.csv_file_path}. Categories loaded: {len(self.CATEGORIES)}")

    def get_CATEGORIES(self):
        return sorted(list(self.CATEGORIES)) # Return sorted list for consistent dropdown order

    def load_existing_data(self):
        try:
            if self.csv_file_path.exists() and self.csv_file_path.stat().st_size > 0:
                # CORRECTED: Treat 'date' column as string to maintain 'dd/mm/YYYY' format
                df = pd.read_csv(self.csv_file_path, dtype={'date': str})
                app_logger.info(f"Loaded existing data from {self.csv_file_path}. Shape: {df.shape}")
                # Ensure all required columns exist, add if missing (for schema evolution)
                expected_columns = ["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"]
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = None # Or appropriate default
                        app_logger.warning(f"Column '{col}' was missing in {self.csv_file_path}. Added with None values.")
                return df
            else:
                app_logger.info(f"No existing data file found at {self.csv_file_path} or file is empty. Creating new DataFrame.")
                return pd.DataFrame(
                    columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
        except pd.errors.EmptyDataError:
            app_logger.warning(f"EmptyDataError while reading {self.csv_file_path}. Returning empty DataFrame.")
            return pd.DataFrame(
                columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
        except Exception as e:
            app_logger.error(f"Error loading data from {self.csv_file_path}: {e}", exc_info=True)
            messagebox.showerror("Error Loading Data", f"Error loading data from {self.csv_file_path}: {e}")
            return pd.DataFrame(
                columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])

    def log_activity(self, program, window, start_time_epoch, end_time_epoch, total_time_seconds):
        # CORRECTED: Use string dates consistently
        current_date_str = time.strftime('%d/%m/%Y')
        start_time_str = time.strftime('%H:%M:%S', time.localtime(start_time_epoch))
        end_time_str = time.strftime('%H:%M:%S', time.localtime(end_time_epoch))
        total_time_minutes = round(total_time_seconds / 60, 2)

        category = self.category_map.get(program, "Misc") # Default to Misc if not found

        self.log.append([current_date_str, program, window, category,
                         start_time_str, end_time_str, total_time_minutes, "0%"]) # Placeholder for percent
        
        app_logger.debug(f"Activity logged (in memory): Date={current_date_str}, Prog={program}, Win={window}, Cat={category}, Start={start_time_str}, End={end_time_str}, TotalMin={total_time_minutes}")
        self.save_log_to_csv()


    def save_log_to_csv(self):
        if not self.log:
            app_logger.debug("save_log_to_csv called but self.log is empty. Nothing to save.")
            return

        new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
        self.log = [] # Clear in-memory log after converting to DataFrame

        try:
            # Ensure directories exist (might be redundant if main did it, but good for safety)
            config.HISTORICAL_LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
            config.REPORTS_DIR_PATH.mkdir(parents=True, exist_ok=True)

            perform_archival_check = not self.df.empty and not new_df.empty
            archived_this_save = False

            if perform_archival_check:
                try:
                    # Use first date from current df and first from new_df for month check
                    df_first_date_str = self.df['date'].iloc[0]
                    new_df_first_date_str = new_df['date'].iloc[0]

                    df_date_obj = datetime.strptime(df_first_date_str, '%d/%m/%Y').date()
                    new_log_date_obj = datetime.strptime(new_df_first_date_str, '%d/%m/%Y').date()
                    
                    app_logger.debug(f"Date check for archival: Existing DF month = {df_date_obj.month}, New log month = {new_log_date_obj.month}")

                    if df_date_obj.month != new_log_date_obj.month:
                        app_logger.info(f"Month change detected. Archiving old log for month {df_date_obj.month}/{df_date_obj.year}.")
                        now = datetime.now()
                        
                        # Archive existing self.df
                        archive_log_filename = config.HISTORICAL_LOG_DIR_PATH / f"log_{df_date_obj.year}{df_date_obj.month:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}.csv"
                        # Recalculate percentages for the df about to be archived
                        df_to_archive = self.calculate_session_percentages(self.df.copy()) # Operate on a copy
                        df_to_archive.to_csv(archive_log_filename, index=False, date_format='%d/%m/%Y') # date_format if dates were objects
                        app_logger.info(f"Archived log to {archive_log_filename}")

                        # Create report from archived df
                        df_work_hours = df_to_archive.groupby(['date', 'category'])['total_time'].sum().reset_index()
                        report_filename = config.REPORTS_DIR_PATH / f"report_{df_date_obj.year}{df_date_obj.month:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}.csv"
                        df_work_hours.to_csv(report_filename, index=False)
                        app_logger.info(f"Generated report {report_filename}")
                        
                        self.df = new_df # Start new df with new_df
                        archived_this_save = True
                    else:
                        self.df = pd.concat([self.df, new_df], ignore_index=True)
                except IndexError:
                    app_logger.warning("IndexError during archival check (df or new_df might be empty despite initial check). Appending new data.", exc_info=True)
                    self.df = pd.concat([self.df, new_df], ignore_index=True) if not self.df.empty else new_df
                except Exception as e:
                    app_logger.error(f"Error during archival logic: {e}. Appending new data.", exc_info=True)
                    self.df = pd.concat([self.df, new_df], ignore_index=True) if not self.df.empty else new_df
            else: # self.df was empty, so just use new_df
                self.df = new_df
                app_logger.info("Current DataFrame was empty. Initialized with new log data.")

            # Calculate percentages for the (potentially updated or new) self.df
            if not self.df.empty:
                self.df = self.calculate_session_percentages(self.df)
                self.df.to_csv(self.csv_file_path, index=False) # date_format not strictly needed if dates are strings
                app_logger.info(f"Saved updated log to {str(self.csv_file_path).split("\\")[-1]}. DF shape: {self.df.shape}. Program: {self.df['program'].iloc[-1] if not self.df.empty else 'N/A'}")
            else:
                app_logger.warning("DataFrame is empty after processing, nothing to save to main log file.")

        except Exception as e:
            app_logger.error(f"Failed to save log to CSV: {e}", exc_info=True)
            # Fallback: try to append raw log if DF operations failed, to not lose data
            try:
                fallback_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
                if not fallback_df.empty: # if self.log was already cleared, this will be empty
                    fallback_df.to_csv(self.csv_file_path, mode='a', header=not self.csv_file_path.exists(), index=False)
                    app_logger.info(f"Fallback: Appended raw log entries to {self.csv_file_path}")
                    self.log = [] # Ensure cleared if appended
            except Exception as fe:
                app_logger.error(f"Fallback save also failed: {fe}", exc_info=True)


    def calculate_session_percentages(self, df_input):
        df = df_input.copy() # Work on a copy
        if df.empty:
            app_logger.debug("calculate_session_percentages called with empty DataFrame.")
            return df

        # Ensure 'date', 'start_time', 'end_time' are present and not all NaT/None
        if not all(col in df.columns for col in ['date', 'start_time', 'end_time']):
            app_logger.error("Missing required columns for percentage calculation.")
            return df_input # Return original if columns missing

        try:
            # Convert time strings to datetime.time objects for proper subtraction
            # Date is already a string 'dd/mm/YYYY'
            df['start_datetime'] = pd.to_datetime(df['date'] + ' ' + df['start_time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            df['end_datetime'] = pd.to_datetime(df['date'] + ' ' + df['end_time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

            # Handle potential NaT from conversion errors
            df.dropna(subset=['start_datetime', 'end_datetime'], inplace=True)
            if df.empty:
                app_logger.warning("DataFrame became empty after coercing date/times for percentage calculation.")
                return df_input # Return original if all rows had errors


            # Calculate duration in seconds
            df['total_time_seconds_calc'] = (df['end_datetime'] - df['start_datetime']).dt.total_seconds()
            
            # Group by date to calculate session totals
            df['session_total_time_seconds'] = df.groupby('date')['total_time_seconds_calc'].transform('sum')

            # Calculate percentage
            df['percent_calc'] = (df['total_time_seconds_calc'] / df['session_total_time_seconds']) * 100
            df['percent'] = df['percent_calc'].round(2).astype(str) + "%"
            
            # Fill NaN percentages that might occur if session_total_time_seconds is 0 (though unlikely with proper data)
            df['percent'] = df['percent'].fillna("0.00%")


            df.drop(columns=['start_datetime', 'end_datetime', 'total_time_seconds_calc', 'session_total_time_seconds', 'percent_calc'], inplace=True, errors='ignore')
            app_logger.debug("Session percentages calculated.")
            return df
        except Exception as e:
            app_logger.error(f"Error in calculate_session_percentages: {e}", exc_info=True)
            return df_input # Return original DataFrame on error

#   region New Window entry

    def get_category(self, window_name_key): # Renamed to avoid conflict with 'category' variable
        # This function creates its own Tkinter root temporarily, which is generally not ideal
        # if the main app already has one. However, for a modal dialog, it can work.
        # Consider making this a Toplevel window of the main root if possible.
        dialog_root = tk.Tk()
        dialog_root.withdraw()  # Hide the dummy root window

        category_window = tk.Toplevel(dialog_root)
        category_window.configure(bg=self.theme.windowBg())
        category_window.title(f"Categorize: {window_name_key}")
        category_window.attributes("-topmost", True) # Keep on top
        timer_icon_path_str = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str):
            try:
                category_window.iconbitmap(timer_icon_path_str)
            except tk.TclError as e:
                app_logger.warning(f"Failed to set timer icon ({timer_icon_path_str}): {e}. Using default.")
        else:
            app_logger.warning(f"Timer icon not found at {timer_icon_path_str}. Using default.")

        # Center the window (simple centering)
        category_window.update_idletasks()
        width = 400
        height = 250
        x = (category_window.winfo_screenwidth() // 2) - (width // 2)
        y = (category_window.winfo_screenheight() // 2) - (height // 2)
        category_window.geometry(f'{width}x{height}+{x}+{y}')


        tk.Label(category_window, text=f"Enter category for '{window_name_key}':", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "12", "bold")).pack(pady=10)
        
        tk.Label(category_window, text="Available categories:", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "10")).pack(pady=(5,0))

        category_var = tk.StringVar()
        # Use sorted categories for dropdown
        category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=self.get_CATEGORIES(), state="readonly", width=30)
        category_dropdown.pack(pady=5)

        tk.Label(category_window, text="OR Enter new category:", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "10")).pack(pady=(10,0))
        
        new_category_entry = tk.Entry(category_window, bg=self.theme.buttonBg(), fg="white", width=33)
        new_category_entry.pack(pady=5)

        result = {"category": "Misc"} # Default result

        def submit_category():
            selected_category = category_dropdown.get()
            new_category = new_category_entry.get().strip().title() # Capitalize new categories

            final_category = "Misc" # Default
            if new_category: # Prioritize new entry
                final_category = new_category
                if final_category not in self.CATEGORIES:
                    self.CATEGORIES.add(final_category)
                    app_logger.info(f"New category added: {final_category}")
            elif selected_category:
                final_category = selected_category
            else:
                messagebox.showwarning("No Category", "No category selected or entered. Defaulting to 'Misc'.", parent=category_window)
                # Keep dialog open if nothing is chosen:
                # category_window.deiconify()
                # return 
            
            result["category"] = final_category
            self.category_map[window_name_key] = final_category
            self.save_dict_to_txt(str(config.USER_PROGRAMS_FILE_PATH))
            app_logger.info(f"Program '{window_name_key}' categorized as '{final_category}'")
            category_window.destroy()
            dialog_root.destroy()


        submit_button = tk.Button(category_window, text="Submit", command=submit_category, bg=self.theme.buttonBg(),
                                  fg="white", font=("Helvetica", "10", "bold"),
                                  activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        submit_button.pack(pady=10)

        new_category_entry.bind("<Return>", lambda event: submit_category())
        # category_dropdown.bind("<Return>", lambda event: submit_category()) # Combobox doesn't typically submit on enter like this
        submit_button.bind("<Return>", lambda event: submit_category())
        
        def on_dialog_close():
            # Handle if user closes dialog with 'X'
            app_logger.warning(f"Category dialog for '{window_name_key}' closed without submission. Defaulting to 'Misc'.")
            self.category_map[window_name_key] = "Misc" # Ensure it's mapped to avoid re-prompting immediately
            self.save_dict_to_txt(str(config.USER_PROGRAMS_FILE_PATH))
            category_window.destroy()
            dialog_root.destroy()

        category_window.protocol("WM_DELETE_WINDOW", on_dialog_close)
        category_window.grab_set() # Make modal
        dialog_root.wait_window(category_window) # Wait for category_window to be destroyed

        return result["category"]
    
    def save_dict_to_txt(self, file_path_str): # CORRECTED: takes path
        """Save category_map to a text file in JSON format."""
        try:
            with open(file_path_str, "w") as file:
                json.dump(self.category_map, file, indent=4)
            app_logger.info(f"Category map saved to {file_path_str}")
        except IOError as e:
            app_logger.error(f"Failed to save category map to {file_path_str}: {e}", exc_info=True)

    def load_dict_from_txt(self, file_path_str): # CORRECTED: takes path
        """Load category_map from the text file if it exists, otherwise return an empty dict."""
        file_path = Path(file_path_str)
        if file_path.exists() and file_path.stat().st_size > 0:
            try:
                with open(file_path, "r") as file:
                    loaded_map = json.load(file)
                    app_logger.info(f"Category map loaded from {file_path_str}")
                    return loaded_map
            except json.JSONDecodeError as e:
                app_logger.error(f"Error decoding JSON from {file_path_str}: {e}. Returning empty map.", exc_info=True)
                return {}
            except IOError as e:
                app_logger.error(f"IOError reading {file_path_str}: {e}. Returning empty map.", exc_info=True)
                return {}
        app_logger.info(f"Category map file {file_path_str} not found or empty. Returning empty map.")
        return {}
    
    def open_edit_program_categories_window(self, parent_root):
        app_logger.debug("Opening edit program categories window.")
        edit_window = tk.Toplevel(parent_root)
        edit_window.title("Edit Program Categories")
        edit_window.configure(bg=self.theme.windowBg())
        edit_window.transient(parent_root)
        edit_window.grab_set() # Make modal
        edit_window.minsize(width=450, height=400) # Adjusted minsize for new elements

        timer_icon_path_str = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str):
            try:
                edit_window.iconbitmap(timer_icon_path_str)
            except tk.TclError as e:
                app_logger.warning(f"Failed to set timer icon ({timer_icon_path_str}): {e}. Using default.")
        else:
            app_logger.warning(f"Timer icon not found at {timer_icon_path_str}. Using default.")

        # --- Main frame for scrollable list ---
        # This frame will contain the canvas and scrollbar
        list_container_frame = tk.Frame(edit_window, bg=self.theme.windowBg())
        list_container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        canvas = tk.Canvas(list_container_frame, bg=self.theme.windowBg(), highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollable_frame = tk.Frame(canvas, bg=self.theme.windowBg())
        canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def configure_canvas_window(event):
            canvas.itemconfig(canvas_window_id, width=event.width)

        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_window)

        # --- Mousewheel Scrolling Functionality ---
        def _on_mousewheel_scroll(event):
            scroll_intensity = 0
            if hasattr(event, 'delta') and event.delta != 0:  # Windows/macOS
                scroll_intensity = int(-1 * (event.delta / 120))
            elif event.num == 4:  # Linux scroll up
                scroll_intensity = -1
            elif event.num == 5:  # Linux scroll down
                scroll_intensity = 1

            if scroll_intensity != 0:
                canvas.yview_scroll(scroll_intensity, "units")
            
            # If the widget that triggered this is a Combobox, prevent its own scroll action.
            if isinstance(event.widget, ttk.Combobox):
                return "break" # Prevents the combobox from changing value on scroll

        def _bind_mousewheel_to_widget(widget):
            widget.bind("<MouseWheel>", _on_mousewheel_scroll)
            widget.bind("<Button-4>", _on_mousewheel_scroll)
            widget.bind("<Button-5>", _on_mousewheel_scroll)

        _bind_mousewheel_to_widget(canvas)
        _bind_mousewheel_to_widget(scrollable_frame)
        # Child widgets inside scrollable_frame will be bound in _populate_program_list

        available_categories = [] # Predefined categories
        for i in self.CATEGORIES:
            available_categories.append(i)
        
        # This dictionary will store StringVars for comboboxes in the list
        # It's a member of the class (self.program_vars) to be accessible by helper methods
        self.program_vars.clear() 

        def _populate_program_list():
            # Clear existing widgets from scrollable_frame
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            self.program_vars.clear() # Clear for repopulation

            # Header
            header_font = ("Helvetica", "10", "bold")
            header_bg = self.theme.windowBg()
            header_fg = 'white'
            
            ttk.Label(scrollable_frame, text="Program Name", font=header_font, background=header_bg, foreground=header_fg).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            ttk.Label(scrollable_frame, text="Category", font=header_font, background=header_bg, foreground=header_fg).grid(row=0, column=1, padx=5, pady=5, sticky="w")

            row_num = 1
            sorted_programs = sorted(self.category_map.items())

            for program_name, current_category in sorted_programs:
                label_bg = self.theme.windowBg()
                label_fg = 'white'

                program_label = ttk.Label(scrollable_frame, text=program_name, background=label_bg, foreground=label_fg)
                program_label.grid(row=row_num, column=0, padx=5, pady=3, sticky="w")
                _bind_mousewheel_to_widget(program_label)
                
                category_var = tk.StringVar(value=current_category)
                
                category_combo = ttk.Combobox(scrollable_frame, textvariable=category_var, values=available_categories, state="readonly", width=17)
                if current_category in available_categories:
                    category_combo.set(current_category)
                elif available_categories: # Default to first if current not valid or not in list
                    category_combo.set(available_categories[0])
                
                category_combo.grid(row=row_num, column=1, padx=5, pady=3, sticky="ew")
                _bind_mousewheel_to_widget(category_combo)
                
                self.program_vars[program_name] = category_var
                row_num += 1
            
            scrollable_frame.columnconfigure(0, weight=1) 
            scrollable_frame.columnconfigure(1, weight=0) 

            # Update canvas scrollregion after populating.
            # Defer this to ensure all widgets are drawn and bbox is correct.
            canvas.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        # --- New Entry Frame (for adding/updating programs) ---
        new_entry_outer_frame = tk.Frame(edit_window, bg=self.theme.windowBg())
        new_entry_outer_frame.pack(fill=tk.X, padx=10, pady=(0, 5)) # pady=(top, bottom)

        # Add a separator or a label for this section
        ttk.Separator(new_entry_outer_frame, orient='horizontal').pack(fill='x', pady=(2, 5))
        section_label = ttk.Label(new_entry_outer_frame, text="Add or Update Program in List", font=("Helvetica", "10", "italic"), background=self.theme.windowBg(), foreground='white')
        section_label.pack(pady=(0,5))


        new_entry_fields_frame = tk.Frame(new_entry_outer_frame, bg=self.theme.windowBg())
        new_entry_fields_frame.pack(fill=tk.X)

        ttk.Label(new_entry_fields_frame, text="Program Name:", background=self.theme.windowBg(), foreground='white').grid(row=0, column=0, padx=5, pady=3, sticky="w")
        new_program_name_var = tk.StringVar()
        new_program_name_entry = ttk.Entry(new_entry_fields_frame, textvariable=new_program_name_var, width=30)
        new_program_name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(new_entry_fields_frame, text="Category:", background=self.theme.windowBg(), foreground='white').grid(row=1, column=0, padx=5, pady=3, sticky="w")
        new_program_category_var = tk.StringVar()
        new_program_category_combo = ttk.Combobox(new_entry_fields_frame, textvariable=new_program_category_var, values=available_categories, state="readonly", width=17)
        if available_categories: new_program_category_combo.set(available_categories[0]) # Default selection
        new_program_category_combo.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        def add_or_update_program_in_list():
            prog_name = new_program_name_var.get().strip()
            prog_cat = new_program_category_var.get()

            if not prog_name:
                messagebox.showwarning("Input Error", "Program name cannot be empty.", parent=edit_window)
                return
            if not prog_cat: # Should not happen with readonly combobox if categories exist
                messagebox.showwarning("Input Error", "Please select a category.", parent=edit_window)
                return

            self.category_map[prog_name] = prog_cat
            _populate_program_list() # Refresh the entire list display

            new_program_name_var.set("") # Clear input field
            if available_categories: new_program_category_combo.set(available_categories[0]) # Reset combobox
            app_logger.info(f"Program '{prog_name}' added/updated in UI list. Click 'Save Changes' to persist.")
            new_program_name_entry.focus_set() # Set focus back to entry for quick additions

        add_update_button = tk.Button(new_entry_fields_frame, text="Add / Update in List", command=add_or_update_program_in_list,
                                     bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "9"),
                                     activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=1, relief=tk.SOLID)
        add_update_button.grid(row=0, column=2, rowspan=2, padx=(10,5), pady=3, sticky="nswe") # Span 2 rows

        new_entry_fields_frame.columnconfigure(1, weight=1) # Allow entry and combobox to expand

        # Initial population of the list
        _populate_program_list()

        # --- Buttons Frame (Save/Cancel) ---
        buttons_frame = tk.Frame(edit_window, bg=self.theme.windowBg())
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,10), padx=10)

        def save_program_categories_and_close():
            updated_count = 0
            # Iterate through self.program_vars which reflects the current state of comboboxes
            for program_name, category_var in self.program_vars.items():
                new_category = category_var.get()
                # Check if this program is still in category_map (it should be if list is synced)
                # and if its category has changed from what's in category_map (which might have been updated by "Add/Update")
                # The primary source of truth for saving should be what's currently in the UI's StringVars
                if program_name in self.category_map and self.category_map[program_name] != new_category :
                    self.category_map[program_name] = new_category # Update the main map
                    updated_count +=1
                elif program_name not in self.category_map: # Should not happen if Add/Update syncs map
                    self.category_map[program_name] = new_category
                    updated_count +=1


            # An alternative: self.category_map is already updated by "Add/Update Program in List".
            # Here, we just need to ensure any changes made *directly in the list's comboboxes* are captured.
            # The current self.program_vars reflects all items shown in the list.
            temp_map_from_ui = {}
            changes_made_in_list = False
            for prog_name_in_var, cat_var in self.program_vars.items():
                ui_category = cat_var.get()
                temp_map_from_ui[prog_name_in_var] = ui_category
                if self.category_map.get(prog_name_in_var) != ui_category:
                    changes_made_in_list = True
            
            if changes_made_in_list or updated_count > 0 : # updated_count for new items via add/update form
                                                           # changes_made_in_list for direct combobox changes
                # Consolidate: update self.category_map from temp_map_from_ui
                # This ensures that what you see in the UI is what gets saved.
                # Count actual changes against the original state before opening the window, or just save the current state.
                # For simplicity, let's assume self.category_map is the state to save,
                # and it has been updated by both the "Add/Update" form and direct combobox changes (via program_vars).

                # Rebuild category_map based on the UI's current state (program_vars)
                final_map_to_save = {}
                final_updated_count = 0
                original_map_snapshot = dict(self.category_map) # Take a snapshot before this window modified it (if needed for precise count)
                                                                # For this example, we'll just count based on current self.category_map vs program_vars

                for pn, cv in self.program_vars.items():
                    new_cat = cv.get()
                    final_map_to_save[pn] = new_cat
                    if original_map_snapshot.get(pn) != new_cat: # Compare to original state if available
                        final_updated_count +=1
                
                # If items were deleted from category_map by some other means and list not refreshed, they'd be lost.
                # Current design: list always reflects category_map. So, program_vars is the authority for save.
                self.category_map = final_map_to_save # Update the master map to what's in UI

                self.save_dict_to_txt(str(config.USER_PROGRAMS_FILE_PATH))
                self.update_csv_log() # Assuming this is a method of your class
                app_logger.info(f"Program categories updated and saved. Total items: {len(self.category_map)}.")
                messagebox.showinfo("Success", f"Program categories saved successfully!", parent=edit_window)
            else:
                messagebox.showinfo("No Changes", "No category changes were made to save.", parent=edit_window)
            
            edit_window.destroy()

        save_button = tk.Button(buttons_frame, text="Save Changes", command=save_program_categories_and_close,
                                bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "10", "bold"),
                                activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=2)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = tk.Button(buttons_frame, text="Cancel", command=edit_window.destroy,
                                  bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "10"),
                                  activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=2)
        cancel_button.pack(side=tk.RIGHT, padx=5)

        edit_window.protocol("WM_DELETE_WINDOW", edit_window.destroy) # Ensure clean close

        # Center the window
        parent_root.update_idletasks()
        x = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - (edit_window.winfo_width() // 2)
        y = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        new_program_name_entry.focus_set() # Initial focus on the new program name entry

    def update_csv_log(self):
        update_df = self.df.copy()
        #self.category_map = self.load_dict_from_txt(str(config.USER_PROGRAMS_FILE_PATH)) # Ensure this is loaded

        if not isinstance(self.category_map, dict):
            print("Error: self.category_map is not a dictionary. Aborting update.")
            return # Or raise an error

        changes_made = False
        for index, row_data in update_df.iterrows(): # Use index and row_data for clarity
            program_name = row_data['program']
            current_category = row_data['category']

            # Safely get the new category from the map
            # Provide a default or handle missing keys appropriately
            new_category = self.category_map.get(program_name)

            if new_category is None:
                print(f"Warning: Program '{program_name}' not found in category_map. setting 'Misc'.")
                update_df.loc[index, 'category'] = 'Misc' #  <--- CORRECT WAY TO MODIFY
                changes_made = True

            if current_category != new_category:
                print(f"'{program_name}': Category '{current_category}' will change to '{new_category}'")
                update_df.loc[index, 'category'] = new_category #  <--- CORRECT WAY TO MODIFY
                changes_made = True

        if changes_made:
            print("Saving updated CSV...")
            update_df.to_csv(self.csv_file_path, index=False)
            self.df = self.load_existing_data() # Reload the newly saved data
            print("CSV updated and data reloaded.")
        else:
            print("No changes detected. CSV not modified.")
            # Optionally, you might still want to reload if the file could have been changed externally
            # self.df = self.load_existing_data()
        
        

# ADDED: Method to get all data (current + historical)
    def get_all_logged_data(self):
        app_logger.info("Consolidating all logged data.")
        # Load historical data
        historical_dfs = []
        historical_log_dir = config.HISTORICAL_LOG_DIR_PATH
        
        if historical_log_dir.exists():
            csv_files = list(historical_log_dir.glob("*.csv"))
            app_logger.debug(f"Found {len(csv_files)} historical CSV files in {historical_log_dir}")
            for file_path in csv_files:
                try:
                    df_hist_single = pd.read_csv(file_path, dtype={'date': str}) # Keep date as string
                    if not df_hist_single.empty:
                        historical_dfs.append(df_hist_single)
                except Exception as e:
                    app_logger.error(f"Error reading historical CSV {file_path} for report: {e}", exc_info=True)
        
        all_data_frames = historical_dfs
        
        # Add current logger's DataFrame if it's not empty
        if self.df is not None and not self.df.empty:
            all_data_frames.append(self.df.copy()) # Use a copy of the current df

        if not all_data_frames:
            app_logger.warning("No data found (current or historical) for report generation.")
            return pd.DataFrame()

        combined_df = pd.concat(all_data_frames, ignore_index=True)
        app_logger.info(f"Consolidated data for report. Total entries: {len(combined_df)}")
        
        # Ensure 'date' column is consistently string 'dd/mm/YYYY' before any conversion attempt
        # This should already be the case due to dtype={'date': str} on reads and strftime on writes.
        # For robust date filtering, convert to datetime objects
        try:
            combined_df['parsed_date'] = pd.to_datetime(combined_df['date'], format='%d/%m/%Y', errors='coerce')
        except Exception as e:
            app_logger.error(f"Error parsing 'date' column to datetime objects: {e}. Report may be incomplete or inaccurate.", exc_info=True)
            # Fallback or return empty if critical
            return pd.DataFrame() # Or handle rows with NaT in parsed_date

        return combined_df

    # ADDED: Method to generate and export the report
    def export_activity_report(self, export_type="all", start_date_str=None, end_date_str=None):
        app_logger.info(f"Exporting activity report. Type: {export_type}, Start: {start_date_str}, End: {end_date_str}")
        
        all_data = self.get_all_logged_data()

        if all_data.empty:
            messagebox.showinfo("No Data", "No data available to generate a report.", parent=None) # Consider passing parent from UI
            return

        report_df = all_data.copy()

        if export_type == "range":
            if start_date_str and end_date_str:
                try:
                    # Convert UI input strings to datetime objects for comparison
                    # Assuming UI provides dates in 'dd/mm/YYYY' or a DateEntry widget provides datetime
                    start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
                    end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
                    
                    # Filter based on the 'parsed_date' column
                    # Ensure end_date is inclusive by setting time to end of day or comparing just dates
                    report_df = report_df[
                        (report_df['parsed_date'].notna()) &
                        (report_df['parsed_date'] >= start_date) & 
                        (report_df['parsed_date'] <= pd.Timestamp(end_date).replace(hour=23, minute=59, second=59))
                    ]
                    app_logger.debug(f"Filtered data for range. Entries after filtering: {len(report_df)}")
                except ValueError:
                    messagebox.showerror("Date Error", "Invalid date format. Please use DD/MM/YYYY.", parent=None)
                    app_logger.error("Invalid date format provided for report range.", exc_info=True)
                    return
                except Exception as e:
                    messagebox.showerror("Filtering Error", f"Error filtering data by date: {e}", parent=None)
                    app_logger.error(f"Error filtering data by date: {e}", exc_info=True)
                    return
            else:
                messagebox.showwarning("Date Range Missing", "Please specify both start and end dates for a ranged report.", parent=None)
                return
        
        if report_df.empty:
            messagebox.showinfo("No Data", "No data found for the selected criteria.", parent=None)
            return

        # Generate the summary report: sum of 'total_time' grouped by 'date' (original string) and 'category'
        # Drop the temporary 'parsed_date' before grouping if you want the original string 'date' in output
        summary_report = report_df.drop(columns=['parsed_date'], errors='ignore') 
        summary_report = summary_report.groupby(['date', 'category'])['total_time'].sum().reset_index()
        
        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Report As",
            initialdir=str(config.REPORTS_DIR_PATH), # Set initial directory to reports folder
        )

        if file_path:
            try:
                summary_report.to_csv(file_path, index=False)
                messagebox.showinfo("Report Exported", f"Report successfully exported to:\n{file_path}", parent=None)
                app_logger.info(f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report: {e}", parent=None)
                app_logger.error(f"Failed to save report to {file_path}: {e}", exc_info=True)
        else:
            app_logger.info("Report export cancelled by user.")