import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import glob
import os
from tkinter import messagebox 

class GraphDisplay:
    def __init__(self, logger, theme):
        self.logger = logger
        self.theme = theme
        self.is_open = False
        self.df_all_data = self.get_history()

    def show_graph(self, df):
        self.df_all_data = self.get_history()
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
        
        if df.empty and not self.df_all_data.empty:
            messagebox.showinfo("No data to display.")
            return

        try:
            #df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
            print(f"show graph \n{df.head()}\n")
            #df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
            print(f"show graph \n{df.head()}\n")
            today = pd.Timestamp.today().normalize().strftime("%d/%m/%Y")
            df_today = df[df["date"] == today]

            if df_today.empty:
                print("No data for today.")
                return
            
            df_month = df.copy()

            if not self.df_all_data.empty:
                df = pd.concat([self.df_all_data, df], ignore_index=True)
                
            
            category_var = tk.StringVar()
            
            total_time_all = df["total_time"].sum()
            
            total_time_today = df_today["total_time"].sum()
            #total_time_month = df_month["total_time"].sum()
            total_days_month = df_month["date"].nunique()
            total_days = df["date"].nunique()

            df_filter_month = df_month[df_month["category"] == category_var.get()]
            month_work_hours = df_filter_month["total_time"].sum() if not df_filter_month.empty else df_month['total_time'].sum()
            month_work_hours = month_work_hours / 60
            productivity_month = (month_work_hours / (total_days_month * 24 * (2 / 3))) * 100 if month_work_hours > 0 and total_days_month * 24 > 0 else 0
            
            df_filter = df[df["category"] == category_var.get()]
            total_work_hours = df_filter["total_time"].sum() if not df_filter.empty else df['total_time'].sum()
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
                df_filter_day = df_today[df_today["category"] == category_var.get()]
                day_work_hours = df_filter_day["total_time"].sum() if not df_filter_day.empty else df_today['total_time'].sum()
                day_work_hours = day_work_hours / 60
                #productivity_month = (day_work_hours / (total_days_month * 24 * (2 / 3))) * 100 if day_work_hours > 0 and total_days_month * 24 > 0 else 0

                df_filter_month = df_month[df_month["category"] == category_var.get()]
                month_work_hours = df_filter_month["total_time"].sum() if not df_filter_month.empty else df_month['total_time'].sum()
                month_work_hours = month_work_hours / 60
                productivity_month = (month_work_hours / (total_days_month * 24 * (2 / 3))) * 100 if month_work_hours > 0 and total_days_month * 24 > 0 else 0
                #total_time_today = df_today["total_time"].sum()
                #total_days = df["date"].nunique()
                df_filter = df[df["category"] == category_var.get()]
                total_work_hours = df_filter["total_time"].sum() if not df_filter.empty else df['total_time'].sum()
                total_work_hours = total_work_hours / 60
                productivity = (total_work_hours / (total_days * 24 * (2 / 3))) * 100 if total_work_hours > 0 and total_days * 24 > 0 else 0
                info_label.config(
                                    text=f"""Today Session: {day_work_hours:.2f} | This Month: {month_work_hours:.2f} | Active Days During This Month: {total_days_month} | This Month Productivity: {productivity_month:.1f}% (Assuming 8 hours sleep zZzZ)
                                    \nTotal Days: {total_days} | Total {category_var.get()} Hours: {total_work_hours:.2f} | Total Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)"""
                                    )
            
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

            info_label = tk.Label(
                                    info_frame,
                                    text=f"""Today Session: {total_time_today/60:.2f} | This Month: {month_work_hours:.2f} | Active Days During This Month: {total_days_month} | This Month Productivity: {productivity_month:.1f}% (Assuming 8 hours sleep zZzZ)
                                    \nTotal Days: {total_days} | Total {category_var.get()} Hours: {total_work_hours:.2f} | Total Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)""",
                                    font=("Helvetica", 12), bg=self.theme.windowBg(), fg="white"
                                    )
            info_label.grid(row=0, column=1, rowspan=3, padx=10)

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

    def get_history(self):
        try:
            # Use glob to find all CSV files in the folder
            csv_files = glob.glob(os.path.join('C:\\timeLog\\log', "*.csv"))

            if not csv_files:
                print(f"No CSV files found in C:\\timeLog\\log'")
                return pd.DataFrame(columns=None, index=None, dtype=None)

            # Read each CSV into a DataFrame and store in a list
            dfs = []
            for file in csv_files:
                try:
                    df = pd.read_csv(file)#, dayfirst=True) # Parse the 'date' column
                    #df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
                    dfs.append(df)
                except Exception as e:
                    print(f"Error reading {file}: {e}")

            if not dfs: # check if any dataframe was successfully read.
                return pd.DataFrame(columns=None, index=None, dtype=None)

            # Concatenate all DataFrames into a single DataFrame
            merged_df = pd.concat(dfs, ignore_index=True)

            # Set the 'date' column as the index
            #merged_df.set_index('date', inplace=True)

            # Sort the index for consistent ordering
            merged_df.sort_index(inplace=True)

            return merged_df

        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame(columns=None, index=None, dtype=None)