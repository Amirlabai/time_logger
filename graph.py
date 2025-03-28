import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class GraphDisplay:
    def __init__(self, logger, theme):
        self.logger = logger
        self.theme = theme
        self.is_open = False

    def show_graph(self, df):
        def format_with_hours(value):
            """Formats a time value to include "hours"."""
            if value < 60:
                return f"{round(value,2)} minutes"
            else:
                return f"{round(value/60,2)} hours"
    
        def get_top_ten(df):
            try:
                value_counts = df.groupby(["program", "category"])["total_time"].sum()
                top_10 = value_counts.sort_values(ascending=False).head(10)
                top_10_df = top_10.reset_index(name="Total Time")
                return top_10_df
            except KeyError:
                return f"no data found in DataFrame."
        
        if df.empty:
            print("No data to display.")
            return

        try:
            df["date"] = pd.to_datetime(df["date"])
            today = pd.Timestamp.today().normalize()
            df_today = df[df["date"] == today]

            if df_today.empty:
                print("No data for today.")
                return
            
            category_var = tk.StringVar()
            
            total_time_all = df["total_time"].sum()
            
            total_time_today = df_today["total_time"].sum()
            total_days = df["date"].nunique()
            df_filter = df[df["category"] == category_var.get()]
            total_work_hours = df_filter["total_time"].sum() if not df_filter.empty else 0
            total_work_hours = total_work_hours / 60
            productivity = (total_work_hours / (total_days * 24 * (2 / 3))) * 100 if total_work_hours > 0 and total_days * 24 > 0 else 0

            category_time_today = df_today.groupby("category")["total_time"].sum()
            category_time_all = df.groupby("category")["total_time"].sum()
            category_percentage_today = (category_time_today / total_time_today) * 100
            category_percentage_all = (category_time_all / total_time_all) * 100

            all_categories = set(category_percentage_today.index) | set(category_percentage_all.index)
            category_percentage_today = category_percentage_today.reindex(all_categories, fill_value=0)
            category_percentage_all = category_percentage_all.reindex(all_categories, fill_value=0)
            category_percentage_today = category_percentage_today.sort_values(ascending=False)
            category_percentage_all = category_percentage_all[category_percentage_today.index]

            graph_window = tk.Toplevel()
            graph_window.iconbitmap("icons\\barchart_32.ico")
            graph_window.configure(bg=self.theme.windowBg())
            graph_window.title("Category Percentage Comparison")
            

            info_frame = tk.Frame(graph_window, bg=self.theme.windowBg())
            info_frame.pack(pady=(5, 5))

            def update_header():
                total_time_today = df_today["total_time"].sum()
                total_days = df["date"].nunique()
                df_filter = df[df["category"] == category_var.get()]
                total_work_hours = df_filter["total_time"].sum() if not df_filter.empty else 0
                total_work_hours = total_work_hours / 60
                productivity = (total_work_hours / (total_days * 24 * (2 / 3))) * 100 if total_work_hours > 0 and total_days * 24 > 0 else 0
                info_label.config(text=f"Today Session: {round(total_time_today/60,2)} | Total Days: {total_days} | Total {category_var.get()} Hours: {total_work_hours:.2f} | Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)")
            
            def on_catagory_change(event):
                nonlocal df, df_filter
                selected_value = category_dropdown.get()
                category_var.set(selected_value)
                df_filter = df[df["category"] == category_var.get()]
                update_header()

            category_dropdown = ttk.Combobox(
                info_frame, textvariable=category_var, values=list(self.logger.get_CATEGORIES()),state="readonly"   
            )
            category_dropdown.grid(row=0,column=0,padx=10)

            category_dropdown.bind("<<ComboboxSelected>>", on_catagory_change)

            info_label = tk.Label(info_frame,
                                    text=f"Today Session: {round(total_time_today/60,2)} | Total Days: {total_days} | Total {category_var.get()} Hours: {total_work_hours:.2f} | Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)",
                                    font=("Helvetica", 12), bg=self.theme.windowBg(), fg="white")
            info_label.grid(row=0,column=1,padx=10)

            sub_info_frame = tk.Frame(graph_window, bg=self.theme.buttonBg())
            sub_info_frame.pack(pady=(5, 5),padx=10)

            top_ten_frame = tk.Frame(sub_info_frame, bg=self.theme.activeButtonBg(),borderwidth=0)
            top_ten_frame.grid(row=0,column=0,pady=7,padx=7)

            Graph_frame = tk.Frame(sub_info_frame, bg=self.theme.buttonBg())
            Graph_frame.grid(row=0,column=1,rowspan=2,pady=7,padx=7)
            
            top_ten = get_top_ten(df)

            if isinstance(top_ten, pd.DataFrame): # Check if get_top_ten returned a dataframe
                # Create labels for each row
                program_label = tk.Label(top_ten_frame, text='program', anchor='w', justify='left',
                                            font=("Helvetica", 14, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                program_label.grid(row=0, columnspan=2, column=0, padx=2, pady=2, sticky='w')

                category_label = tk.Label(top_ten_frame, text='category', anchor='w', justify='left',
                                        font=("Helvetica", 12, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                category_label.grid(row=0, column=2, padx=2, pady=2, sticky='w')

                time_label = tk.Label(top_ten_frame, text='Total Time', anchor='w', justify='left',
                                    font=("Helvetica", 12, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                time_label.grid(row=0, column=3, padx=2, pady=2, sticky='w')
                for index, row in top_ten.iterrows():
                    program_label = tk.Label(top_ten_frame, text=row['program'], anchor='w', justify='left',
                                            font=("Helvetica", 12, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                    program_label.grid(row=index+1, columnspan=2, column=0, padx=2, pady=2, sticky='w')

                    category_label = tk.Label(top_ten_frame, text=row['category'], anchor='w', justify='left',
                                            font=("Helvetica", 12, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                    category_label.grid(row=index+1, column=2, padx=2, pady=2, sticky='w')

                    time_label = tk.Label(top_ten_frame, text=format_with_hours(row['Total Time']), anchor='w', justify='left',
                                        font=("Helvetica", 12, "bold"), bg=self.theme.activeButtonBg(), fg="white")
                    time_label.grid(row=index+1, column=3, padx=2, pady=2, sticky='w')
            else:
                print("error")
                # Handle the case where get_top_ten returned an error message
                top_ten_label = tk.Label(top_ten_frame,
                                            text=f"{top_ten.to_string()}", anchor='n', justify='left',
                                            font=("Helvetica", 12, "bold"), bg=self.theme.buttonBg(), fg="white")
                top_ten_label.grid(row=0, column=0, padx=2, pady=2)

            fig, ax = plt.subplots(figsize=(9,5), facecolor=self.theme.buttonBg())
            canvas = FigureCanvasTkAgg(fig, master=Graph_frame)
            canvas.get_tk_widget().grid(row=0,column=2,rowspan=2,pady=7,padx=7)

            bar_width = 0.4
            x_labels = list(category_percentage_today.index)
            x_positions = range(len(x_labels))

            ax.bar(x_positions, category_percentage_today, width=bar_width, label="Today", color='skyblue')
            ax.bar([x + bar_width for x in x_positions], category_percentage_all, width=bar_width, label="Overall", color='orange')

            for i, v in enumerate(category_percentage_today):
                ax.text(x_positions[i], v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold', color="white")

            for i, v in enumerate(category_percentage_all):
                ax.text(x_positions[i] + bar_width, v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold', color="white")

            ax.set_facecolor(self.theme.windowBg())
            ax.set_ylabel("Percentage (%)", color="white")
            ax.set_xlabel("Categories", color="white")
            ax.set_title("Category Percentage (Today vs Overall)", fontweight='bold', color="white")
            ax.set_xticks([x + bar_width / 2 for x in x_positions])
            ax.set_xticklabels(x_labels, rotation=25, ha="right", fontsize=10, color="white")
            ax.tick_params(axis='y', colors='white')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.legend()

            fig.tight_layout()
            canvas.draw()

            def close_graph():
                graph_window.destroy()
                self.is_open = False

            close_button = tk.Button(graph_window, text="Close", command=close_graph, bg=self.theme.buttonBg(), fg="white", font=("Arial", "10", "bold"),
                                 activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
            close_button.pack(pady=5)

            self.is_open = True

        except Exception as e:
            print(f"Error showing graph: {e}")
