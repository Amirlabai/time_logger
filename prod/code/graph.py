import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import os
from pathlib import Path
from datetime import datetime # For date manipulations

import config
from app_logger import app_logger

class GraphDisplay:
    def __init__(self, logger_instance, theme):
        self.logger = logger_instance 
        self.theme = theme
        self.is_open = False
        self.graph_window_title = "Category Percentage Comparison"
        app_logger.info("GraphDisplay initialized (SQLite mode).")

    def _fetch_and_prepare_data(self):
        """Fetches all data from the logger and performs initial preparation."""
        app_logger.debug("GraphDisplay: Fetching all data from logger.")
        df_all_entries = self.logger.get_all_logged_data()

        if df_all_entries.empty:
            app_logger.warning("GraphDisplay: No data returned from logger.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame() 

        df_all_entries['total_time_minutes'] = pd.to_numeric(df_all_entries['total_time_minutes'], errors='coerce').fillna(0)
        df_all_entries['parsed_date'] = pd.to_datetime(df_all_entries['date_text'], format='%d/%m/%Y', errors='coerce')
        df_all_entries.dropna(subset=['parsed_date'], inplace=True)

        if df_all_entries.empty:
            app_logger.warning("GraphDisplay: Data became empty after date parsing/filtering.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        today_dt = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        current_month_start = today_dt.replace(day=1)

        df_today = df_all_entries[df_all_entries['parsed_date'] == today_dt].copy()
        df_this_month = df_all_entries[df_all_entries['parsed_date'] >= current_month_start].copy()
        
        app_logger.info(f"GraphDisplay: Data prepared. Today: {len(df_today)} entries, Month: {len(df_this_month)} entries, Overall: {len(df_all_entries)} entries.")
        return df_today, df_this_month, df_all_entries

    def show_graph(self):
        app_logger.info("GraphDisplay: show_graph called.")
        
        df_today, df_this_month, df_overall = self._fetch_and_prepare_data()
        
        if df_overall.empty:
            messagebox.showinfo("No Data", "No current or historical data available to display.", 
                                parent=None if not self.is_open else plt.get_current_fig_manager().window)
            app_logger.warning("GraphDisplay: Graph requested, but no data found after fetching.")
            return
        
        def format_time_display(total_minutes):
            if pd.isna(total_minutes) or total_minutes == 0: return "0 minutes"
            if total_minutes < 1: return f"{total_minutes * 60:.0f} seconds"
            if total_minutes < 60: return f"{total_minutes:.1f} minutes"
            return f"{total_minutes / 60:.2f} hours"
    
        def get_top_ten_programs(df_source):
            if df_source.empty or 'program_name' not in df_source.columns or 'total_time_minutes' not in df_source.columns:
                app_logger.warning("get_top_ten_programs: DataFrame empty or missing required columns.")
                return pd.DataFrame(columns=["program_name", "category", "Total Time (min)"])
            try:
                value_counts = df_source.groupby(["program_name", "category"])["total_time_minutes"].sum()
                top_10 = value_counts.nlargest(10)
                top_10_df = top_10.reset_index(name="Total Time (min)")
                app_logger.debug(f"Top ten programs calculated. Found: {len(top_10_df)}")
                return top_10_df
            except KeyError as e:
                app_logger.error(f"KeyError in get_top_ten_programs: {e}", exc_info=True)
                return pd.DataFrame(columns=["program_name", "category", "Total Time (min)"])

        graph_window = None # Define for except block
        try:
            category_var = tk.StringVar(value="All Categories")
            
            graph_window = tk.Toplevel() 
            graph_window.title(self.graph_window_title)
            graph_window.configure(bg=self.theme.windowBg())
            graph_window.minsize(800, 600) # Set a reasonable minsize

            barchart_icon_path_str = str(config.BARCHART_ICON_PATH)
            if os.path.exists(barchart_icon_path_str):
                try: graph_window.iconbitmap(barchart_icon_path_str)
                except tk.TclError as e: app_logger.warning(f"Failed to set barchart icon for graph window: {e}")
            else: app_logger.warning(f"Barchart icon not found for graph window: {barchart_icon_path_str}")
            
            self.is_open = True
            graph_window.protocol("WM_DELETE_WINDOW", lambda: self.close_graph_window(graph_window))

            info_frame = tk.Frame(graph_window, bg=self.theme.windowBg())
            info_frame.pack(pady=10, padx=10, fill="x")
            info_label = tk.Label(info_frame, text="Calculating stats...", justify="left", font=("Helvetica", 10), bg=self.theme.windowBg(), fg="white")
            info_label.pack(side="left", fill="x", expand=True)
            
            available_categories = ["All Categories"] + self.logger.get_CATEGORIES()
            category_dropdown = ttk.Combobox(info_frame, textvariable=category_var, values=available_categories, state="readonly", width=25)
            category_dropdown.pack(side="left", padx=10)
            category_dropdown.set("All Categories")

            def update_displayed_stats():
                selected_cat = category_var.get()
                app_logger.debug(f"Updating stats for selected category: {selected_cat}")

                df_today_stat = df_today[(df_today['category'] == selected_cat) if selected_cat != "All Categories" else (df_today['category'] != "Break")]
                df_month_stat = df_this_month[(df_this_month['category'] == selected_cat) if selected_cat != "All Categories" else (df_this_month['category'] != "Break")]
                
                if selected_cat == "All Categories":
                    df_overall_stat = df_overall[df_overall['category'] != "Break"]
                else:
                    df_overall_stat = df_overall[df_overall['category'] == selected_cat]

                time_today_cat = df_today_stat['total_time_minutes'].sum()
                time_month_cat = df_month_stat['total_time_minutes'].sum()
                days_month_active = df_month_stat['parsed_date'].nunique() if not df_month_stat.empty else 0
                time_overall_cat = df_overall_stat['total_time_minutes'].sum()
                days_overall_active = df_overall_stat['parsed_date'].nunique() if not df_overall_stat.empty else 0
                
                prod_month = ((time_month_cat / 60) / (days_month_active * 16) * 100) if days_month_active > 0 and (time_month_cat > 0) else 0
                prod_overall = ((time_overall_cat / 60) / (days_overall_active * 16) * 100) if days_overall_active > 0 and (time_overall_cat > 0) else 0
                
                cat_display_name = f"{selected_cat}" if selected_cat != "All Categories" else "Productive"

                stats_text = (
                    f"Displaying for: {cat_display_name}\n"
                    f"Today: {format_time_display(time_today_cat)}\n"
                    f"This Month: {format_time_display(time_month_cat)} ({days_month_active} active day(s)). Productivity: {prod_month:.1f}%\n"
                    f"Overall: {format_time_display(time_overall_cat)} ({days_overall_active} total day(s) with data). Productivity: {prod_overall:.1f}%"
                )
                info_label.config(text=stats_text, anchor='w')
            
            category_dropdown.bind("<<ComboboxSelected>>", lambda event: update_displayed_stats())
            update_displayed_stats()

            content_frame = tk.Frame(graph_window, bg=self.theme.buttonBg())
            content_frame.pack(pady=10, padx=10, fill="both", expand=True)

            top_ten_outer_frame = tk.Frame(content_frame, bg=self.theme.activeButtonBg(), relief="sunken", borderwidth=1)
            top_ten_outer_frame.pack(side="left", fill="y", padx=(0,5), pady=5, ipadx=5, ipady=5)
            
            tk.Label(top_ten_outer_frame, text='Top Programs (Overall Time)',
                     font=("Helvetica", 11, "bold"), bg=self.theme.activeButtonBg(), fg="white").pack(pady=(5,10))

            top_ten_canvas = tk.Canvas(top_ten_outer_frame, bg=self.theme.activeButtonBg(), highlightthickness=0, width=300) 
            top_ten_canvas.pack(side="left", fill="both", expand=True)

            top_ten_scrollbar = ttk.Scrollbar(top_ten_outer_frame, orient="vertical", command=top_ten_canvas.yview)
            top_ten_scrollbar.pack(side="right", fill="y")
            
            top_ten_canvas.configure(yscrollcommand=top_ten_scrollbar.set)
            
            top_ten_inner_frame = tk.Frame(top_ten_canvas, bg=self.theme.activeButtonBg())
            top_ten_canvas.create_window((0, 0), window=top_ten_inner_frame, anchor="nw", tags="inner_frame")

            def _configure_inner_frame_width(event):
                top_ten_canvas.itemconfig('inner_frame', width=event.width)
            top_ten_canvas.bind('<Configure>', _configure_inner_frame_width)
            
            def _update_scrollregion(event):
                 top_ten_canvas.configure(scrollregion=top_ten_canvas.bbox("all"))
            top_ten_inner_frame.bind("<Configure>", _update_scrollregion)

            top_ten_data = get_top_ten_programs(df_overall) 

            for widget in top_ten_inner_frame.winfo_children():
                widget.destroy()

            if not top_ten_data.empty:
                tk.Label(top_ten_inner_frame, text='Program', font=("Helvetica", 9, "bold"), 
                         bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=0, padx=2, pady=1, sticky='nw')
                tk.Label(top_ten_inner_frame, text='Category', font=("Helvetica", 9, "bold"), 
                         bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=1, padx=2, pady=1, sticky='nw')
                tk.Label(top_ten_inner_frame, text='Time', font=("Helvetica", 9, "bold"), 
                         bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=0, column=2, padx=2, pady=1, sticky='ne')
                
                for index, row_data in top_ten_data.iterrows():
                    program_display_name = str(row_data['program_name'])[:25] # Max length
                    category_display_name = str(row_data['category'])[:15]
                    time_display = format_time_display(row_data['Total Time (min)'])

                    tk.Label(top_ten_inner_frame, text=program_display_name, font=("Consolas", 8), 
                             bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=0, padx=2, pady=1, sticky='w')
                    tk.Label(top_ten_inner_frame, text=category_display_name, font=("Consolas", 8), 
                             bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=1, padx=2, pady=1, sticky='w')
                    tk.Label(top_ten_inner_frame, text=time_display, font=("Consolas", 8), 
                             bg=self.theme.activeButtonBg(), fg="white", anchor='w').grid(row=index + 1, column=2, padx=2, pady=1, sticky='e')
            else:
                tk.Label(top_ten_inner_frame, text="No program data for top ten.", 
                         font=("Helvetica", 10), bg=self.theme.activeButtonBg(), fg="white").pack(padx=5, pady=5)
            
            top_ten_inner_frame.update_idletasks() 
            top_ten_canvas.config(scrollregion=top_ten_canvas.bbox("all"))
            
            graph_plot_frame = tk.Frame(content_frame, bg=self.theme.windowBg()) # Match theme
            graph_plot_frame.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
            
            fig, ax = plt.subplots(figsize=(7, 5), facecolor=self.theme.windowBg()) # Adjusted figsize
            canvas = FigureCanvasTkAgg(fig, master=graph_plot_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True)

            total_time_today_all_cats = df_today['total_time_minutes'].sum()
            cat_time_today = df_today.groupby("category")["total_time_minutes"].sum()
            cat_perc_today = (cat_time_today / total_time_today_all_cats * 100) if total_time_today_all_cats > 0 else pd.Series(dtype='float64')

            total_time_overall_all_cats = df_overall['total_time_minutes'].sum()
            cat_time_overall = df_overall.groupby("category")["total_time_minutes"].sum()
            cat_perc_overall = (cat_time_overall / total_time_overall_all_cats * 100) if total_time_overall_all_cats > 0 else pd.Series(dtype='float64')

            all_plot_categories = sorted(list(set(cat_perc_today.index) | set(cat_perc_overall.index)))
            cat_perc_today = cat_perc_today.reindex(all_plot_categories, fill_value=0)
            cat_perc_overall = cat_perc_overall.reindex(all_plot_categories, fill_value=0)

            bar_width = 0.35
            x_positions = range(len(all_plot_categories))

            ax.bar([x - bar_width/2 for x in x_positions], cat_perc_today, width=bar_width, label="Today", color='skyblue', edgecolor='black')
            ax.bar([x + bar_width/2 for x in x_positions], cat_perc_overall, width=bar_width, label="Overall", color='orange', edgecolor='black')

            for i, val_today in enumerate(cat_perc_today):
                if val_today > 0.1: 
                    ax.text(x_positions[i] - bar_width/2, val_today + 0.5, f"{val_today:.1f}%", 
                            ha='center', va='bottom', fontsize=7, color="white", fontweight='bold')
            
            for i, val_overall in enumerate(cat_perc_overall):
                if val_overall > 0.1: 
                    ax.text(x_positions[i] + bar_width/2, val_overall + 0.5, f"{val_overall:.1f}%", 
                            ha='center', va='bottom', fontsize=7, color="white", fontweight='bold')

            ax.set_facecolor(self.theme.activeButtonBg()) # Darker background for plot area
            ax.set_ylabel("Percentage of Time (%)", color="white", fontsize=9)
            ax.set_xlabel("Categories", color="white", fontsize=9)
            ax.set_title("Category Time Percentage (Today vs Overall)", fontweight='bold', color="white", fontsize=11)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(all_plot_categories, rotation=25, ha="right", fontsize=8, color="white") # Adjusted rotation
            ax.tick_params(axis='y', colors='white', labelsize=8)
            ax.tick_params(axis='x', colors='white', labelsize=8)
            legend = ax.legend(facecolor=self.theme.buttonBg(), labelcolor="white", edgecolor="gray")
            legend.get_frame().set_alpha(None) # Make legend background solid
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='gray') # Slightly more visible grid
            
            fig.tight_layout(pad=1.5) 
            canvas.draw()
            app_logger.info("Graph drawn successfully.")

            close_button_frame = tk.Frame(graph_window, bg=self.theme.windowBg())
            close_button_frame.pack(fill=tk.X, pady=(5,10))
            close_button = tk.Button(close_button_frame, text="Close Graph", command=lambda: self.close_graph_window(graph_window), 
                                     bg=self.theme.closeButtonBg(), fg="white", font=("Arial", "10", "bold"),
                                     activebackground=self.theme.closeActiveButtonBg(), activeforeground="white", borderwidth=2)
            close_button.pack() # Centered by default in its own frame

        except Exception as e:
            app_logger.error(f"Error showing graph: {e}", exc_info=True)
            messagebox.showerror("Graph Error", f"An error occurred while generating the graph: {e}", 
                                 parent=graph_window if graph_window and graph_window.winfo_exists() else None)
            if self.is_open and graph_window and graph_window.winfo_exists(): # Check if graph_window was successfully created
                graph_window.destroy()
            self.is_open = False

    def close_graph_window(self, window_instance):
        if window_instance and window_instance.winfo_exists():
            window_instance.destroy()
        self.is_open = False
        app_logger.info("Graph window closed.")