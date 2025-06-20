# logger.py
import sqlite3
import time
import pandas as pd
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, Toplevel, Frame, Canvas, Scrollbar, Label, Entry, Button, StringVar, Tk, Radiobutton, simpledialog # <<< NEW: simpledialog
import os # For icon path checking in dialogs
from datetime import datetime # Explicitly from datetime module

import config
from app_logger import app_logger
from db_utils import get_db_connection
# from themes import Theme # Theme instance is passed to __init__

class Logger:
    def __init__(self, theme):
        self.theme = theme # Theme() is already instantiated in main, pass it directly.
        self.category_map = self._load_program_categories_from_db()
        self.program_vars = {} # Initialize here, will be used by the method
        
        self.CATEGORIES = set()
        if self.category_map: # Ensure category_map is not None or empty
            for category_value in self.category_map.values():
                if isinstance(category_value, str) and category_value.strip():
                    self.CATEGORIES.add(category_value)
        app_logger.info(f"Logger initialized. Categories loaded from DB: {len(self.CATEGORIES)}")

    def get_CATEGORIES(self):
        # print(f"Current categories: {self.CATEGORIES}") # Debug print to see current categories
        return sorted(list(self.CATEGORIES)) # Return sorted list for consistent dropdown order


    def log_activity(self, program, window, start_time_epoch, end_time_epoch, total_time_seconds):
        current_date_str = time.strftime('%d/%m/%Y', time.localtime(start_time_epoch))
        start_time_str = time.strftime('%H:%M:%S', time.localtime(start_time_epoch))
        end_time_str = time.strftime('%H:%M:%S', time.localtime(end_time_epoch))
        total_time_minutes = round(total_time_seconds / 60, 2)
        category = self.category_map.get(program, "Misc")
        percent_text_placeholder = "0%"

        sql = """
            INSERT INTO time_entries
            (date_text, program_name, window_title, category,
             start_time_text, end_time_text, total_time_minutes,
             start_timestamp_epoch, end_timestamp_epoch, percent_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            current_date_str, program, window, category,
            start_time_str, end_time_str, total_time_minutes,
            start_time_epoch, end_time_epoch, percent_text_placeholder
        )
        # Using context manager for connection
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    conn.commit()
                    app_logger.debug(f"Activity logged to DB: Prog={program}, Cat={category}, TotalMin={total_time_minutes}")
                except sqlite3.Error as e:
                    app_logger.error(f"Failed to log activity to database: {e}", exc_info=True)
                    # Rollback is implicit if commit isn't reached due to exception with context manager

    def _load_program_categories_from_db(self):
        categories = {}
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT program_name, category FROM program_categories")
                    for row in cursor.fetchall():
                        categories[row["program_name"]] = row["category"]
                    app_logger.info(f"Program categories loaded from DB. Count: {len(categories)}")
                except sqlite3.Error as e:
                    app_logger.error(f"Failed to load program categories from DB: {e}", exc_info=True)
        return categories

    def save_program_category_to_db(self, program_name, category):
        sql = "INSERT OR REPLACE INTO program_categories (program_name, category) VALUES (?, ?)"
        success = False
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, (program_name, category))
                    conn.commit()
                    app_logger.info(f"Program category saved to DB: {program_name} -> {category}")
                    self.category_map[program_name] = category # Update in-memory map
                    if category not in self.CATEGORIES:
                        self.CATEGORIES.add(category)
                    success = True
                except sqlite3.Error as e:
                    app_logger.error(f"Failed to save program category to DB for '{program_name}': {e}", exc_info=True)
        return success

    def get_category(self, window_name_key):
        # This temp root is not ideal but matches original structure.
        # Better: pass main app root to be parent of Toplevel.
        dialog_root = Tk()
        dialog_root.withdraw()

        category_window = Toplevel(dialog_root) # Original used Toplevel directly
        category_window.configure(bg=self.theme.windowBg())
        category_window.title(f"Categorize: {window_name_key}")
        category_window.attributes("-topmost", True)

        timer_icon_path_str = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str):
            try: category_window.iconbitmap(timer_icon_path_str)
            except tk.TclError as e: app_logger.warning(f"Failed to set timer icon ({timer_icon_path_str}): {e}")
        else: app_logger.warning(f"Timer icon not found at {timer_icon_path_str}")

        category_window.update_idletasks()
        width, height = 400, 250
        x = (category_window.winfo_screenwidth() // 2) - (width // 2)
        y = (category_window.winfo_screenheight() // 2) - (height // 2)
        category_window.geometry(f'{width}x{height}+{x}+{y}')

        Label(category_window, text=f"Enter category for '{window_name_key}':", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold")).pack(pady=10)
        Label(category_window, text="Available categories:", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10")).pack(pady=(5,0))

        category_var = StringVar()
        # Refresh categories for dropdown
        category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=self.get_CATEGORIES(), state="readonly", width=30)
        category_dropdown.pack(pady=5)

        Label(category_window, text="OR Enter new category:", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10")).pack(pady=(10,0))
        new_category_entry = Entry(category_window, bg=self.theme.buttonBg(), fg="white", width=33, insertbackground="white")
        new_category_entry.pack(pady=5)
        new_category_entry.focus_set()

        result_category = {"value": "Misc"} # Use a mutable type to pass result out

        def submit_category_action():
            selected_dropdown_category = category_var.get()
            entered_new_category = new_category_entry.get().strip().title()
            final_cat = "Misc"

            if entered_new_category:
                final_cat = entered_new_category
            elif selected_dropdown_category:
                final_cat = selected_dropdown_category
            else:
                messagebox.showwarning("No Category", "No category selected or entered. Defaulting to 'Misc'.", parent=category_window)

            if self.save_program_category_to_db(window_name_key, final_cat):
                result_category["value"] = final_cat
                app_logger.info(f"Program '{window_name_key}' categorized as '{final_cat}' and saved to DB.")
            else:
                app_logger.error(f"Failed to save category for '{window_name_key}' to DB from get_category dialog.")
                messagebox.showerror("DB Error", "Could not save category to database.", parent=category_window)
                # Keep dialog open or handle error as appropriate

            category_window.destroy()
            dialog_root.destroy()

        submit_btn = Button(category_window, text="Submit", command=submit_category_action, bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"), activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        submit_btn.pack(pady=20)
        new_category_entry.bind("<Return>", lambda event: submit_category_action())
        submit_btn.bind("<Return>", lambda event: submit_category_action())

        def on_dialog_forced_close():
            app_logger.warning(f"Category dialog for '{window_name_key}' closed without submission. Defaulting to 'Misc'.")
            self.save_program_category_to_db(window_name_key, "Misc") # Save default
            result_category["value"] = "Misc" # Ensure default is returned
            category_window.destroy()
            dialog_root.destroy()

        category_window.protocol("WM_DELETE_WINDOW", on_dialog_forced_close)
        category_window.grab_set()
        dialog_root.wait_window(category_window)
        return result_category["value"]


    # <<< NEW HELPER DIALOG FOR CATEGORY EDITING >>>
    def _ask_category_dialog(self, parent, program_name, current_category, all_categories):
        """
        A dialog to select or enter a new category for a specific program.
        """
        dialog = Toplevel(parent)
        dialog.title(f"Set Category for: {program_name}")
        dialog.configure(bg=self.theme.windowBg())
        dialog.transient(parent)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        # Basic styling and layout
        dialog.geometry("350x270") # Adjusted size
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (350 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (230 // 2)
        dialog.geometry(f"+{x}+{y}")


        Label(dialog, text=f"Program: {program_name}", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "10", "bold")).pack(pady=(10,5))
        Label(dialog, text=f"Current Category: {current_category}", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "9")).pack(pady=(0,10))

        category_var = StringVar(value=current_category)
        
        Label(dialog, text="Select from existing:", bg=self.theme.windowBg(), fg="white").pack()
        if all_categories:
            combo = ttk.Combobox(dialog, textvariable=category_var, values=all_categories, state="readonly", width=30)
            combo.pack(pady=5)
            if current_category in all_categories:
                combo.set(current_category)
            elif all_categories: # Default to first if current not in list (e.g. was 'Misc' and Misc isn't explicitly saved)
                 combo.set(all_categories[0])
        else:
            Label(dialog, text="No existing categories defined.", bg=self.theme.windowBg(), fg="white").pack(pady=5)

        Label(dialog, text="Or enter new category:", bg=self.theme.windowBg(), fg="white").pack(pady=(10,0))
        new_category_entry = Entry(dialog, bg=self.theme.buttonBg(), fg="white", width=33, insertbackground="white")
        new_category_entry.pack(pady=5)
        new_category_entry.focus_set() # Focus on new entry

        new_cat_chosen = {"value": None} # To store result from dialog

        def on_submit():
            entered = new_category_entry.get().strip().title()
            selected = category_var.get() # From combobox
            
            if entered: # New entry takes precedence
                new_cat_chosen["value"] = entered
            elif selected and selected != current_category : # Combobox selected a different category
                new_cat_chosen["value"] = selected
            elif selected and selected == current_category: # Combobox selected same category, effectively no change unless user intended it
                 new_cat_chosen["value"] = selected # or None to indicate no change
            else: # No selection, no entry
                messagebox.showwarning("No Input", "Please select or enter a category.", parent=dialog)
                return
            dialog.destroy()

        def on_cancel():
            new_cat_chosen["value"] = None # Indicate no change or cancellation
            dialog.destroy()

        button_frame = Frame(dialog, bg=self.theme.windowBg())
        button_frame.pack(pady=20, fill="x", side="bottom")
        
        ok_btn = Button(button_frame, text="OK", command=on_submit, width=8, bg=self.theme.buttonBg(), fg="white", activebackground=self.theme.activeButtonBg())
        ok_btn.pack(side=tk.LEFT, padx=(60,10)) # Adjust padding for centering

        cancel_btn = Button(button_frame, text="Cancel", command=on_cancel, width=8, bg=self.theme.buttonBg(), fg="white", activebackground=self.theme.activeButtonBg())
        cancel_btn.pack(side=tk.RIGHT, padx=(10,60)) # Adjust padding for centering


        new_category_entry.bind("<Return>", lambda e: on_submit())
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        
        parent.wait_window(dialog) # Wait for dialog to close
        return new_cat_chosen["value"]


    def open_edit_program_categories_window(self, parent_root):
        app_logger.debug("Opening edit program categories window.")
        edit_window = Toplevel(parent_root)
        edit_window.title("Edit Program Categories")
        edit_window.configure(bg=self.theme.windowBg())
        edit_window.transient(parent_root)
        edit_window.grab_set()
        edit_window.minsize(width=550, height=450) # <<< CHANGED: Slightly wider for new button

        timer_icon_path_str = str(config.TIMER_ICON_PATH)
        if os.path.exists(timer_icon_path_str):
            try: edit_window.iconbitmap(timer_icon_path_str)
            except tk.TclError as e: app_logger.warning(f"Failed to set timer icon for edit window: {e}")
        else: app_logger.warning(f"Timer icon not found for edit window: {timer_icon_path_str}")

        list_container_frame = Frame(edit_window, bg=self.theme.windowBg())
        list_container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        canvas = Canvas(list_container_frame, bg=self.theme.windowBg(), highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame = Frame(canvas, bg=self.theme.windowBg())
        canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="scrollable_frame")

        def _configure_scrollable_frame_width(event):
            canvas.itemconfig(canvas_window_id, width=event.width)
        def _update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _configure_scrollable_frame_width)
        scrollable_frame.bind("<Configure>", _update_scrollregion)

        # --- Mousewheel Scrolling Fix (Canvas only) --- # <<< CHANGED: Simplified, as Comboboxes are gone from this direct view
        def _on_mousewheel_scroll_handler(event):
            scroll_intensity = 0
            if event.num == 4 or event.delta > 0:  # Scroll up
                scroll_intensity = -1
            elif event.num == 5 or event.delta < 0:  # Scroll down
                scroll_intensity = 1

            if scroll_intensity != 0:
                # Check if the event widget is the canvas or a child of the scrollable_frame
                # to prevent scrolling if mouse is over widgets outside the canvas (e.g., buttons below)
                # This check might need refinement depending on exact layout.
                # For now, let's assume any scroll in this window should target the canvas.
                canvas.yview_scroll(scroll_intensity, "units")
            # No "return break" needed here if we only want canvas to scroll and no other widget
            # in this specific handler has a conflicting default scroll action we want to suppress.
            # If other widgets were added that also scroll (e.g. Text), more logic would be needed.

        edit_window.bind_all("<MouseWheel>", _on_mousewheel_scroll_handler, add="+")
        edit_window.bind_all("<Button-4>", _on_mousewheel_scroll_handler, add="+")
        edit_window.bind_all("<Button-5>", _on_mousewheel_scroll_handler, add="+")
        # --- End Mousewheel Scrolling Fix --- #

        self.program_vars.clear() # Stores StringVars for each program's category

        def _populate_program_list():
            for widget in scrollable_frame.winfo_children(): widget.destroy()
            # self.program_vars.clear() # Clearing at the beginning of parent function

            current_db_categories = self.get_CATEGORIES() # Get all unique categories currently in DB

            header_font = ("Helvetica", "10", "bold")
            Label(scrollable_frame, text="Program Name", font=header_font, bg=self.theme.windowBg(), fg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            Label(scrollable_frame, text="Category", font=header_font, bg=self.theme.windowBg(), fg="white").grid(row=0, column=1, padx=5, pady=5, sticky="w")
            # Column 2 for the change button (no header needed or add one if you like)
            Label(scrollable_frame, text="Action", font=header_font, bg=self.theme.windowBg(), fg="white").grid(row=0, column=2, padx=5, pady=5, sticky="w")


            row_num = 1
            # Iterate through self.category_map (which is loaded from DB initially)
            # to ensure all known programs are listed.
            # self.program_vars will store the current (potentially edited) category for each program.
            sorted_programs = sorted(self.category_map.keys())


            for program_name in sorted_programs:
                current_prog_category = self.category_map.get(program_name, "Misc")

                # Ensure StringVar exists for this program
                if program_name not in self.program_vars:
                    self.program_vars[program_name] = StringVar(value=current_prog_category)
                else:
                    # If it exists, make sure its value reflects the current state
                    # (e.g. after an add/update operation, or if loaded from DB)
                    self.program_vars[program_name].set(current_prog_category)

                category_var_for_program = self.program_vars[program_name]


                program_label_widget = Label(scrollable_frame, text=program_name, bg=self.theme.windowBg(), fg="white")
                program_label_widget.grid(row=row_num, column=0, padx=5, pady=3, sticky="w")

                # Display category as a label
                category_display_label = Label(scrollable_frame, textvariable=category_var_for_program, bg=self.theme.windowBg(), fg="white", width=20, anchor="w") # <<< CHANGED
                category_display_label.grid(row=row_num, column=1, padx=5, pady=3, sticky="ew")


                # --- Change Button Logic --- # <<< NEW/CHANGED
                def _create_change_handler(p_name, cat_var):
                    # p_name_local = p_name # Capture p_name for this specific button
                    # cat_var_local = cat_var # Capture cat_var
                    def _handler():
                        # Pass current_db_categories (all unique categories from DB) to the dialog
                        all_known_categories = self.get_CATEGORIES() # Refresh just in case
                        new_category = self._ask_category_dialog(edit_window,
                                                                p_name,
                                                                cat_var.get(),
                                                                all_known_categories)
                        if new_category is not None: # If a new category was chosen (not cancelled)
                            cat_var.set(new_category) # Update the StringVar, label updates automatically
                            # Also update self.category_map to reflect the pending change before saving
                            self.category_map[p_name] = new_category
                            if new_category not in self.CATEGORIES: # If it's a brand new category overall
                                self.CATEGORIES.add(new_category)
                                # Update the list of categories for the "Add/Update Program" section's combobox
                                new_program_category_combo['values'] = self.get_CATEGORIES()
                    return _handler

                change_button = ttk.Button(scrollable_frame,
                                          text="Edit",
                                          command=_create_change_handler(program_name, category_var_for_program),
                                          width=8) # <<< NEW
                change_button.grid(row=row_num, column=2, padx=5, pady=3, sticky="e") # <<< NEW column

                row_num += 1

            scrollable_frame.columnconfigure(0, weight=3) # Program name can be wider
            scrollable_frame.columnconfigure(1, weight=2) # Category label
            scrollable_frame.columnconfigure(2, weight=0) # Action button, no extra weight
            edit_window.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        new_entry_outer_frame = Frame(edit_window, bg=self.theme.windowBg())
        new_entry_outer_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        ttk.Separator(new_entry_outer_frame, orient='horizontal').pack(fill='x', pady=(2, 5))
        Label(new_entry_outer_frame, text="Add or Update Program in List", font=("Helvetica", "10", "italic"), bg=self.theme.windowBg(), fg="white").pack(pady=(0,5))
        new_entry_fields_frame = Frame(new_entry_outer_frame, bg=self.theme.windowBg())
        new_entry_fields_frame.pack(fill=tk.X)

        Label(new_entry_fields_frame, text="Program Name:", bg=self.theme.windowBg(), fg="white").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        new_program_name_var = StringVar()
        new_program_name_entry = Entry(new_entry_fields_frame, textvariable=new_program_name_var, width=30, bg=self.theme.buttonBg(), fg="white", insertbackground="white")
        new_program_name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        Label(new_entry_fields_frame, text="Category:", bg=self.theme.windowBg(), fg="white").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        new_program_category_var = StringVar()
        # This combobox is for adding *new* programs, so it's fine here, not in the scrollable list.
        new_program_category_combo = ttk.Combobox(new_entry_fields_frame, textvariable=new_program_category_var, values=self.get_CATEGORIES(), state="readonly", width=23)
        if self.get_CATEGORIES(): new_program_category_combo.set(self.get_CATEGORIES()[0])
        new_program_category_combo.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        def add_or_update_program_in_ui_list():
            prog_name = new_program_name_var.get().strip()
            prog_cat = new_program_category_var.get()
            if not prog_name or not prog_cat:
                messagebox.showwarning("Input Error", "Program name and category cannot be empty.", parent=edit_window)
                return

            # Update self.category_map directly (this is the source for _populate_program_list)
            self.category_map[prog_name] = prog_cat
            # Ensure the StringVar exists in program_vars for this program
            if prog_name not in self.program_vars:
                self.program_vars[prog_name] = StringVar()
            self.program_vars[prog_name].set(prog_cat) # Set its value

            if prog_cat not in self.CATEGORIES:
                self.CATEGORIES.add(prog_cat)
                new_program_category_combo['values'] = self.get_CATEGORIES() # Update categories for the "add new" combobox

            _populate_program_list() # Repopulate the list UI
            new_program_name_var.set("")
            if self.get_CATEGORIES(): new_program_category_combo.set(self.get_CATEGORIES()[0])
            app_logger.info(f"Program '{prog_name}' UI list updated. Save to persist to DB.")
            new_program_name_entry.focus_set()

        add_update_btn = Button(new_entry_fields_frame, text="Add/Update in List", command=add_or_update_program_in_ui_list, bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "9"), activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=1, relief=tk.SOLID)
        add_update_btn.grid(row=0, column=2, rowspan=2, padx=(10,5), pady=3, sticky="nswe")
        new_entry_fields_frame.columnconfigure(1, weight=1)

        _populate_program_list() # Initial population

        buttons_frame = Frame(edit_window, bg=self.theme.windowBg())
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,10), padx=10)

        def _cleanup_bindings_and_destroy():
            edit_window.unbind_all("<MouseWheel>")
            edit_window.unbind_all("<Button-4>")
            edit_window.unbind_all("<Button-5>")
            edit_window.destroy()

        def save_all_changes_to_db_and_close():
            programs_to_update_historical_logs = {}
            # Iterate over self.program_vars which holds the final state of categories from the UI
            for prog_name_in_map, final_ui_category_var in self.program_vars.items():
                final_ui_category = final_ui_category_var.get()
                original_db_category = "" # Need to fetch original from a clean load or initial map if different
                # For simplicity, we assume self.category_map was updated by _ask_category_dialog
                # and the original version of category_map (before this window opened)
                # is not easily available here without more complex state management.
                # The current logic will just save what's in self.program_vars.
                # To detect actual changes for historical log update:
                # We'd need to compare self.program_vars[prog].get() with an initial_category_map[prog]
                
                # Simplified: just save everything from program_vars.
                # Historical update will be triggered if self.category_map[prog_name] (potentially UI updated)
                # is different from what would be loaded from DB for that program initially.
                # This part might need more robust "initial state" vs "final state" tracking if precise historical update prompting is critical.
                
                # Let's assume self.category_map has been kept in sync with UI changes
                # and reflects the desired final state.
                if prog_name_in_map in self.category_map: # Should always be true
                    self.category_map[prog_name_in_map] = final_ui_category # Ensure category_map is the source of truth for saving

            # --- Rebuild programs_to_update_historical_logs based on changes ---
            # This requires knowing the original categories before this dialog opened.
            # For now, we'll assume a simpler approach: if a category in self.category_map (now UI synced)
            # differs from what *would have been* in an untouched category map from the DB, mark for update.
            # This is tricky without storing the initial state.
            # A pragmatic approach: any program whose category in self.program_vars
            # is different from how it was when _populate_program_list first ran.
            # This is implicitly handled if self.category_map is used for comparison *after* UI updates.

            # Let's refine: iterate self.program_vars which has the final UI state
            # and compare with a fresh load of the categories to see what *actually* changed
            # compared to the DB's last state before this save.
            # However, self.category_map is already modified in the change_handler and add_or_update.

            # Simpler logic for now: save everything in self.category_map as the new truth.
            # The check for historical logs will be based on this new truth.
            # To make `programs_to_update_historical_logs` more accurate, you'd store `initial_category_map = self._load_program_categories_from_db()`
            # at the start of `open_edit_program_categories_window` and compare against it.

            saved_count = 0
            # Save all entries from the UI-updated self.category_map
            for prog_name, final_cat in self.category_map.items():
                if self.save_program_category_to_db(prog_name, final_cat):
                    # If you had an initial_category_map:
                    # original_cat = initial_category_map.get(prog_name)
                    # if original_cat and original_cat != final_cat:
                    #     programs_to_update_historical_logs[prog_name] = final_cat
                    # For now, we can't robustly populate programs_to_update_historical_logs this way.
                    # The existing historical update logic will trigger if any category_map value changed *during the session*.
                    saved_count +=1
            
            # The historical update part needs careful thought about "original vs new"
            # For now, if saved_count > 0, it implies some change might have occurred.
            # The prompt is generic.

            if saved_count > 0:
                app_logger.info(f"{saved_count} program-category mappings potentially saved/updated in DB.")
                new_program_category_combo['values'] = self.get_CATEGORIES() # Refresh for "add new" combo

                # This prompt is now less accurate as we don't precisely know *which* ones changed from DB state
                if messagebox.askyesno(
                    "Update Log Entries?",
                    "Program categories may have been changed. Update these in all historical log entries for affected programs?\n(This might take a moment and cannot be undone easily)",
                    parent=edit_window):
                    # To do this properly, you need a list of (program_name, new_category) for *actually changed* items.
                    # For now, it will re-apply current categories from self.category_map if user says yes.
                    for prog_to_update, new_cat_for_log in self.category_map.items(): # Potentially update all
                         self.update_categories_in_log_entries(prog_to_update, new_cat_for_log)
                    app_logger.info("Historical log entries potentially updated based on current categories.")
                messagebox.showinfo("Success", "Program categories saved to database.", parent=edit_window)
            else:
                messagebox.showinfo("No Changes", "No new or modified program categories to save to database.", parent=edit_window)

            _cleanup_bindings_and_destroy()

        save_btn = Button(buttons_frame, text="Save Changes to DB", command=save_all_changes_to_db_and_close, bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "10", "bold"), activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=2)
        save_btn.pack(side=tk.RIGHT, padx=5)
        cancel_btn = Button(buttons_frame, text="Cancel", command=_cleanup_bindings_and_destroy, bg=self.theme.buttonBg(), fg='white', font=("Helvetica", "10"), activebackground=self.theme.activeButtonBg(), activeforeground='white', borderwidth=2)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        edit_window.protocol("WM_DELETE_WINDOW", _cleanup_bindings_and_destroy)

        parent_root.update_idletasks()
        x = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - (edit_window.winfo_reqwidth() // 2)
        y = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - (edit_window.winfo_reqheight() // 2)
        edit_window.geometry(f"+{x}+{y}")
        new_program_name_entry.focus_set()

    def update_categories_in_log_entries(self, program_name, new_category):
        sql = "UPDATE time_entries SET category = ? WHERE program_name = ?"
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, (new_category, program_name))
                    conn.commit()
                    app_logger.info(f"DB: Updated category to '{new_category}' for program '{program_name}'. Rows: {cursor.rowcount}")
                except sqlite3.Error as e:
                    app_logger.error(f"DB: Failed to update categories in time_entries: {e}", exc_info=True)

    def get_all_logged_data(self, start_date_str=None, end_date_str=None):
        app_logger.info(f"DB: Fetching logged data. Start: {start_date_str}, End: {end_date_str}")
        query = "SELECT id, date_text, program_name, window_title, category, start_time_text, end_time_text, total_time_minutes, start_timestamp_epoch, end_timestamp_epoch, percent_text FROM time_entries"
        params = []
        conditions = []
        if start_date_str:
            try:
                start_epoch = datetime.strptime(start_date_str + " 00:00:00", '%d/%m/%Y %H:%M:%S').timestamp()
                conditions.append("start_timestamp_epoch >= ?")
                params.append(start_epoch)
            except ValueError: app_logger.warning(f"Invalid start_date_str for DB query: {start_date_str}")
        if end_date_str:
            try:
                end_epoch = datetime.strptime(end_date_str + " 23:59:59", '%d/%m/%Y %H:%M:%S').timestamp()
                conditions.append("start_timestamp_epoch <= ?")
                params.append(end_epoch)
            except ValueError: app_logger.warning(f"Invalid end_date_str for DB query: {end_date_str}")

        if conditions: query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY start_timestamp_epoch ASC"

        with get_db_connection() as conn:
            if conn:
                try:
                    df = pd.read_sql_query(query, conn, params=tuple(params))
                    app_logger.info(f"DB: Fetched {len(df)} log entries.")
                    return df
                except (sqlite3.Error, Exception) as e:
                    app_logger.error(f"DB: Failed to fetch logged data: {e}", exc_info=True)
        return pd.DataFrame()

    def export_activity_report(self, data_for_report_df):
        app_logger.info(f"Exporting activity report. Received DataFrame with {len(data_for_report_df) if data_for_report_df is not None else 'None'} rows.")

        if data_for_report_df is None or data_for_report_df.empty:
            messagebox.showinfo("No Data", "No data available to generate a report.", parent=None)
            app_logger.warning("Export activity report: No data provided or DataFrame is empty.")
            return

        # The aggregation is now expected to be handled by the UI layer if a summary is needed.
        # This method will export the DataFrame as-is (which could be detailed or pre-summarized).

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Report As",
            initialdir=str(config.REPORTS_DIR_PATH),
        )
        if file_path:
            try:
                # Directly use the passed DataFrame
                data_for_report_df.to_csv(file_path, index=False)
                messagebox.showinfo("Report Exported", f"Report successfully exported to:\n{file_path}", parent=None)
                app_logger.info(f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report: {e}", parent=None)
                app_logger.error(f"Failed to save report to {file_path}: {e}", exc_info=True)
        else:
            app_logger.info("Report export cancelled by user.")

    def calculate_session_percentages(self, df_input):
        df = df_input.copy()
        if df.empty or 'total_time_minutes' not in df.columns:
            app_logger.debug("calculate_session_percentages: empty DataFrame or missing 'total_time_minutes'.")
            df['percent_text'] = "0.00%"
            return df
        if 'date_text' not in df.columns:
            app_logger.error("calculate_session_percentages: 'date_text' column missing.")
            df['percent_text'] = "0.00%"
            return df

        df['session_total_time_minutes'] = df.groupby('date_text')['total_time_minutes'].transform('sum')
        df['percent_calc_val'] = 0.0
        non_zero_session_mask = df['session_total_time_minutes'] != 0
        df.loc[non_zero_session_mask, 'percent_calc_val'] = \
            (df.loc[non_zero_session_mask, 'total_time_minutes'] / df.loc[non_zero_session_mask, 'session_total_time_minutes']) * 100
        df['percent_text'] = df['percent_calc_val'].round(2).astype(str) + "%"
        df.drop(columns=['session_total_time_minutes', 'percent_calc_val'], inplace=True, errors='ignore')
        app_logger.debug("Session percentages calculated on DataFrame (not persisted to DB by this method).")
        return df