import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import glob
import os
from pathlib import Path

# ADDED:
import config
from app_logger import app_logger

class GraphDisplay:
    def __init__(self, logger_instance, theme): # CORRECTED: logger_instance
        self.logger = logger_instance # Use the passed logger object
        self.theme = theme
        self.is_open = False
        # self.df_all_data = self.load_historical_data() # Load historical data once on init or lazily
        app_logger.info("GraphDisplay initialized.")

    def remove_dup_func(self, df):
        # Specify the column to exclude from the duplicate check
        column_to_exclude = 'total_time'

        # Get a list of columns to consider for finding duplicates
        columns_to_consider = df.columns.difference([column_to_exclude])

        # Remove duplicates based on 'columns_to_consider', keeping the first occurrence
        df_deduplicated = df.drop_duplicates(subset=columns_to_consider, keep='first')

        #print("\nDataFrame after removing duplicates (excluding '{}'):".format(column_to_exclude))
        return(df_deduplicated)

    def load_historical_data(self): # Renamed from get_history
        historical_dfs = []
        # CORRECTED: Use configured path
        historical_log_dir = config.HISTORICAL_LOG_DIR_PATH
        
        if not historical_log_dir.exists():
            app_logger.warning(f"Historical log directory not found: {historical_log_dir}")
            return pd.DataFrame()

        csv_files = list(historical_log_dir.glob("*.csv"))
        app_logger.info(f"Found {len(csv_files)} historical CSV files in {historical_log_dir}")

        if not csv_files:
            app_logger.info(f"No historical CSV files found in {historical_log_dir}.")
            return pd.DataFrame()

        for file_path in csv_files:
            try:
                # CORRECTED: Treat 'date' column as string to maintain 'dd/mm/YYYY'
                df = pd.read_csv(file_path, dtype={'date': str})
                if not df.empty:
                    historical_dfs.append(df)
                app_logger.debug(f"Successfully read historical data from {file_path}. Shape: {df.shape}")
            except Exception as e:
                app_logger.error(f"Error reading historical CSV file {file_path}: {e}", exc_info=True)
        
        if not historical_dfs:
            app_logger.info("No data loaded from historical files (all empty or unreadable).")
            return pd.DataFrame()

        merged_df = pd.concat(historical_dfs, ignore_index=True)
        removed_duplicates = self.remove_dup_func(merged_df)
        app_logger.info(f"Removed {len(merged_df) - len(removed_duplicates)} duplicate entries.")
        #print(f"clean {removed_duplicates.shape}, not clean {merged_df.shape}")
        # merged_df.sort_index(inplace=True) # Not needed if index is default range index
        app_logger.info(f"Historical data loaded and merged. Total historical entries: {len(removed_duplicates)}")
        return removed_duplicates

    def show_graph(self, current_day_df_from_logger): # Parameter name changed for clarity
        app_logger.info("show_graph called.")
        
        # Load historical data each time graph is shown to get latest archives, or cache it
        df_historical = self.load_historical_data()
        
        # Combine current session data (passed in) with historical data
        if current_day_df_from_logger.empty and df_historical.empty:
            messagebox.showinfo("No Data", "No current or historical data available to display.", parent=None if not self.is_open else plt.get_current_fig_manager().window)
            app_logger.warning("Graph requested, but no current or historical data found.")
            return
        
        # Ensure 'date' column is string for consistent processing
        current_day_df_from_logger['date'] = current_day_df_from_logger['date'].astype(str)
        if not df_historical.empty:
             df_historical['date'] = df_historical['date'].astype(str)
        
        # df_combined will hold today's data + all historical data for "Overall" stats
        df_combined = pd.concat([df_historical, current_day_df_from_logger], ignore_index=True)
        app_logger.debug(f"Combined DataFrame for graph created. Shape: {df_combined.shape}")

        # df_current_month for "This Month" stats (from current_day_df_from_logger, as it's the live log)
        # Assuming current_day_df_from_logger contains all entries for the current month being logged live
        df_current_month = current_day_df_from_logger.copy()


        def format_time_display(total_minutes): # Renamed from format_with_hours
            if pd.isna(total_minutes): return "0 minutes"
            if total_minutes < 1: return f"{total_minutes * 60:.0f} seconds"
            if total_minutes < 60: return f"{total_minutes:.1f} minutes"
            return f"{total_minutes / 60:.2f} hours"
    
        def get_top_ten_programs(df_source): # Renamed and clarified
            if df_source.empty or 'program' not in df_source.columns or 'total_time' not in df_source.columns:
                app_logger.warning("get_top_ten_programs: DataFrame empty or missing required columns.")
                return pd.DataFrame(columns=["program", "category", "Total Time (min)"]) # Return empty structure
            try:
                # Sum 'total_time' (which is in minutes)
                value_counts = df_source.groupby(["program", "category"])["total_time"].sum()
                top_10 = value_counts.nlargest(10) # Use nlargest for Series
                top_10_df = top_10.reset_index(name="Total Time (min)")
                app_logger.debug(f"Top ten programs calculated. Found: {len(top_10_df)}")
                return top_10_df
            except KeyError:
                app_logger.error("KeyError in get_top_ten_programs.", exc_info=True)
                return pd.DataFrame(columns=["program", "category", "Total Time (min)"])


        try:
            today_str = pd.Timestamp.today().normalize().strftime("%d/%m/%Y")
            # df_today uses only the current_day_df_from_logger for "Today's" specific stats
            df_today = current_day_df_from_logger[current_day_df_from_logger["date"] == today_str].copy()
            app_logger.debug(f"Data for today ({today_str}): {len(df_today)} entries.")

            if df_today.empty and df_combined.empty : # Check if really no data to show
                messagebox.showinfo("No Data", "No data for today or overall to display graphs.", parent=plt.get_current_fig_manager().window if self.is_open else None)
                app_logger.warning("show_graph: df_today is empty and df_combined is also empty. Cannot plot.")
                return

            category_var = tk.StringVar(value="All Categories") # Default to all
            
            # Calculations for "Overall" (df_combined)
            total_time_all_overall = df_combined["total_time"].sum() if not df_combined.empty else 0
            total_days_overall = df_combined["date"].nunique() if not df_combined.empty else 0
            
            # Calculations for "Today" (df_today)
            total_time_minutes_today = df_today["total_time"].sum() if not df_today.empty else 0
            
            # Calculations for "This Month" (df_current_month)
            total_time_minutes_this_month = df_current_month["total_time"].sum() if not df_current_month.empty else 0
            total_days_this_month = df_current_month["date"].nunique() if not df_current_month.empty else 0


            # --- Graph Window Setup ---
            graph_window = tk.Toplevel() # Let Tkinter manage parent if not specified
            graph_window.title("Category Percentage Comparison")
            graph_window.configure(bg=self.theme.windowBg())
            # CORRECTED: Use configured icon path
            barchart_icon_path_str = str(config.BARCHART_ICON_PATH)
            if os.path.exists(barchart_icon_path_str):
                try:
                    graph_window.iconbitmap(barchart_icon_path_str)
                except tk.TclError as e:
                    app_logger.warning(f"Failed to set barchart icon ({barchart_icon_path_str}): {e}. Using default.")
            else:
                app_logger.warning(f"Barchart icon not found: {barchart_icon_path_str}. Using default.")
            
            self.is_open = True # Set flag after window creation
            graph_window.protocol("WM_DELETE_WINDOW", lambda: self.close_graph_window(graph_window))


            # --- Info Frame (Productivity Stats) ---
            info_frame = tk.Frame(graph_window, bg=self.theme.windowBg())
            info_frame.pack(pady=10, padx=10, fill="x")

            info_label = tk.Label(info_frame, text="Calculating stats...", justify="left",
                                  font=("Helvetica", 10), bg=self.theme.windowBg(), fg="white")
            info_label.pack(side="left", fill="x", expand=True)
            
            # Available categories for dropdown from the logger instance (which should be most up-to-date)
            available_categories = ["All Categories"] + self.logger.get_CATEGORIES()

            category_dropdown = ttk.Combobox(info_frame, textvariable=category_var, 
                                             values=available_categories, state="readonly", width=20)
            category_dropdown.pack(side="left", padx=10)
            category_dropdown.set("All Categories") # Default selection

            def update_displayed_stats():
                selected_cat = category_var.get()
                app_logger.debug(f"Updating stats for selected category: {selected_cat}")

                # Filter data based on selected category
                df_today_filtered = df_today[df_today['category'] == selected_cat] if selected_cat != "All Categories" else df_today[df_today['category'] != "Break"]
                df_month_filtered = df_current_month[df_current_month['category'] == selected_cat] if selected_cat != "All Categories" else df_current_month[df_current_month['category'] != "Break"]
                df_overall_filtered = df_combined[df_combined['category'] == selected_cat] if selected_cat != "All Categories" else df_combined

                # Recalculate sums for filtered data
                time_today_cat = df_today_filtered['total_time'].sum() if not df_today_filtered.empty else 0
                time_month_cat = df_month_filtered['total_time'].sum() if not df_month_filtered.empty else 0
                days_month_active = df_month_filtered['date'].nunique() if not df_month_filtered.empty else 0
                
                time_overall_cat = df_overall_filtered['total_time'].sum() if not df_overall_filtered.empty else 0
                days_overall_active = df_overall_filtered['date'].nunique() if not df_overall_filtered.empty else 0
                
                # Productivity calculation (assuming 16 awake hours = 2/3 of a day)
                # Total potential productive time = active_days * 16 hours
                prod_month = ( (time_month_cat / 60) / (days_month_active * 16) * 100 ) if days_month_active > 0 else 0
                prod_overall = ( (time_overall_cat / 60) / (days_overall_active * 16) * 100 ) if days_overall_active > 0 else 0
                
                cat_display_name = f"'{selected_cat}'" if selected_cat != "All Categories" else "Overall"

                stats_text = (
                    f"Displaying for: {cat_display_name}\n"
                    f"Today: {format_time_display(time_today_cat)}\n"
                    f"This Month: {format_time_display(time_month_cat)} ({days_month_active} active day(s)). Productivity: {prod_month:.1f}%\n"
                    f"Overall: {format_time_display(time_overall_cat)} ({days_overall_active} total active day(s)). Productivity: {prod_overall:.1f}%"
                )
                info_label.config(text=stats_text)
                app_logger.debug(f"Productivity stats updated for UI. Category: {selected_cat}")

            category_dropdown.bind("<<ComboboxSelected>>", lambda event: update_displayed_stats())
            update_displayed_stats() # Initial call


            # --- Main Content Frame (Top Ten + Graph) ---
            content_frame = tk.Frame(graph_window, bg=self.theme.buttonBg())
            content_frame.pack(pady=10, padx=10, fill="both", expand=True)

            # --- Top Ten Programs Frame ---
            top_ten_outer_frame = tk.Frame(content_frame, bg=self.theme.activeButtonBg(), relief="sunken", borderwidth=1)
            top_ten_outer_frame.pack(side="left", fill="y", padx=(0,5), pady=5)
            
            tk.Label(top_ten_outer_frame, text='Top 10 Tracked Programs (Overall)',
                     font=("Helvetica", 11, "bold"), bg=self.theme.activeButtonBg(), fg="white").pack(pady=5)

            top_ten_canvas = tk.Canvas(top_ten_outer_frame, bg=self.theme.activeButtonBg(), highlightthickness=0)
            top_ten_canvas.pack(side="left", fill="both", expand=True)

            top_ten_scrollbar = ttk.Scrollbar(top_ten_outer_frame, orient="vertical", command=top_ten_canvas.yview)
            top_ten_scrollbar.pack(side="right", fill="y")
            
            top_ten_canvas.configure(yscrollcommand=top_ten_scrollbar.set)
            top_ten_inner_frame = tk.Frame(top_ten_canvas, bg=self.theme.activeButtonBg())
            top_ten_canvas.create_window((0, 0), window=top_ten_inner_frame, anchor="nw")

            top_ten_data = get_top_ten_programs(df_combined) # Use combined for overall top ten
            if not top_ten_data.empty:
                # Headers
                tk.Label(top_ten_inner_frame, text='Program', font=("Helvetica", 9, "bold"), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=0, padx=2, pady=1, sticky='w')
                tk.Label(top_ten_inner_frame, text='Category', font=("Helvetica", 9, "bold"), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=1, padx=2, pady=1, sticky='w')
                tk.Label(top_ten_inner_frame, text='Time', font=("Helvetica", 9, "bold"), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=2, padx=2, pady=1, sticky='w')
                for index, row_data in top_ten_data.iterrows():
                    tk.Label(top_ten_inner_frame, text=str(row_data['program'])[:20], font=("Consolas", 8), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=0, padx=2, pady=1, sticky='w')
                    tk.Label(top_ten_inner_frame, text=str(row_data['category'])[:15], font=("Consolas", 8), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=1, padx=2, pady=1, sticky='w')
                    tk.Label(top_ten_inner_frame, text=format_time_display(row_data['Total Time (min)']), font=("Consolas", 8), bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=2, padx=2, pady=1, sticky='w')
            else:
                tk.Label(top_ten_inner_frame, text="No program data for top ten.", font=("Helvetica", 10), bg=self.theme.activeButtonBg(), fg="white").pack(padx=5, pady=5)
            
            top_ten_inner_frame.update_idletasks() # Crucial for scrollregion
            top_ten_canvas.config(scrollregion=top_ten_canvas.bbox("all"))


            # --- Matplotlib Graph Frame ---
            graph_plot_frame = tk.Frame(content_frame, bg=self.theme.buttonBg())
            graph_plot_frame.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
            
            fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=self.theme.buttonBg()) # Adjusted size slightly
            canvas = FigureCanvasTkAgg(fig, master=graph_plot_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True)

            if not df_today.empty: # Only plot if there's today data, otherwise overall might be plotted alone
                cat_time_today = df_today.groupby("category")["total_time"].sum()
                cat_perc_today = (cat_time_today / total_time_minutes_today * 100) if total_time_minutes_today > 0 else pd.Series(dtype='float64')
            else: # If df_today is empty, create an empty Series to avoid errors
                cat_perc_today = pd.Series(dtype='float64', index=pd.Index([], name='category'))


            if not df_combined.empty:
                cat_time_overall = df_combined.groupby("category")["total_time"].sum()
                cat_perc_overall = (cat_time_overall / total_time_all_overall * 100) if total_time_all_overall > 0 else pd.Series(dtype='float64')
            else:
                cat_perc_overall = pd.Series(dtype='float64', index=pd.Index([], name='category'))

            # Align categories for plotting
            all_plot_categories = sorted(list(set(cat_perc_today.index) | set(cat_perc_overall.index)))
            cat_perc_today = cat_perc_today.reindex(all_plot_categories, fill_value=0)
            cat_perc_overall = cat_perc_overall.reindex(all_plot_categories, fill_value=0)

            bar_width = 0.35
            x_positions = range(len(all_plot_categories))

            ax.bar([x - bar_width/2 for x in x_positions], cat_perc_today, width=bar_width, label="Today", color='skyblue', edgecolor='black')
            ax.bar([x + bar_width/2 for x in x_positions], cat_perc_overall, width=bar_width, label="Overall", color='orange', edgecolor='black')

            for i, val_today in enumerate(cat_perc_today):
                if val_today > 0.1 : ax.text(x_positions[i] - bar_width/2, val_today + 0.5, f"{val_today:.1f}%", ha='center', va='bottom', fontsize=8, color="white", fontweight='bold')
            for i, val_overall in enumerate(cat_perc_overall):
                 if val_overall > 0.1 : ax.text(x_positions[i] + bar_width/2, val_overall + 0.5, f"{val_overall:.1f}%", ha='center', va='bottom', fontsize=8, color="white", fontweight='bold')

            ax.set_facecolor(self.theme.windowBg())
            ax.set_ylabel("Percentage of Time (%)", color="white", fontsize=10)
            ax.set_xlabel("Categories", color="white", fontsize=10)
            ax.set_title("Category Time Percentage (Today vs Overall)", fontweight='bold', color="white", fontsize=12)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(all_plot_categories, rotation=30, ha="right", fontsize=9, color="white")
            ax.tick_params(axis='y', colors='white', labelsize=9)
            ax.legend(facecolor=self.theme.activeButtonBg(), labelcolor="white", edgecolor="gray")
            ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
            fig.tight_layout() # Adjust layout to prevent labels overlapping
            canvas.draw()
            app_logger.info("Graph drawn successfully.")

            # Close button at the bottom of graph window
            close_button = tk.Button(graph_window, text="Close Graph", command=lambda: self.close_graph_window(graph_window),
                                     bg=self.theme.closeButtonBg(), fg="white", font=("Arial", "10", "bold"),
                                     activebackground=self.theme.closeActiveButtonBg(), activeforeground="white", borderwidth=2)
            close_button.pack(pady=10)

        except Exception as e:
            app_logger.error(f"Error showing graph: {e}", exc_info=True)
            messagebox.showerror("Graph Error", f"An error occurred while generating the graph: {e}", parent=graph_window if self.is_open else None)
            if self.is_open and 'graph_window' in locals() and graph_window.winfo_exists():
                graph_window.destroy() # Close the problematic graph window
            self.is_open = False


    def close_graph_window(self, window_instance):
        if window_instance and window_instance.winfo_exists():
            window_instance.destroy()
        self.is_open = False
        app_logger.info("Graph window closed.")