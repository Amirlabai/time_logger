import pandas as pd
import time
import os
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from themes import Theme
import datetime

class Logger:
    def __init__(self, csv_file,theme):
        self.csv_file = csv_file
        self.theme = Theme()
        self.df = self.load_existing_data()
        self.category_map = {row["program"]: row["category"] for _, row in self.df.iterrows()}
        self.log = []
        self.CATEGORIES = set(self.df['category'].unique())

    def get_CATEGORIES(self):
        return self.CATEGORIES

    def load_existing_data(self):
        try:
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file)
                #self.CATEGORIES.update(df['category'].unique())
                return df
            return pd.DataFrame(
                columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
        except pd.errors.EmptyDataError:
            return pd.DataFrame(
                columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
        except Exception as e:
            messagebox.showerror("Error Loading Data", f"Error loading data: {e}")
            return pd.DataFrame(
                columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])

    def log_activity(self,program, window, start_time, end_time, total_time):
        self.log.append([time.strftime('%Y-%m-%d'),program, window, self.category_map.get(program, "Misc"),
                         time.strftime('%H:%M:%S', time.localtime(start_time)),
                         time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time / 60, 2)])
        self.save_log_to_csv()

    def save_log_to_csv(self):
        try:
            now = datetime.datetime.now()
            df_date = str(self.df.iloc[0,0]).split("-")[1]
            log_date = self.log[0][0].split("-")[1]
            print(df_work_hours)
            if df_date != log_date:
                df_work_hours = self.df.groupby(['date', 'category'])['total_time'].sum()
                df_work_hours.to_csv(f"C:\\timeLog\\report {now.year, now.month}.csv", index=True)
                new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time"])
                new_df = self.calculate_session_percentages(new_df)
                new_df.to_csv(self.csv_file, index=False)
                self.log = []
            else:
                new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time"])
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                self.df = self.calculate_session_percentages(self.df)
                self.df.to_csv(self.csv_file, index=False)
                self.log = []
        except:
            new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time"])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df = self.calculate_session_percentages(self.df)
            self.df.to_csv(self.csv_file, index=False)
            #print(self.log)
            self.log = []
    def calculate_session_percentages(self, df):
        if df.empty:
            return df

        df['date'] = pd.to_datetime(df['date'])
        df['start_time'] = pd.to_datetime(df['start_time'], format='%H:%M:%S').dt.time
        df['end_time'] = pd.to_datetime(df['end_time'], format='%H:%M:%S').dt.time

        df['total_time_seconds'] = df.apply(lambda row: (
            (pd.Timestamp(f'{row["date"]} {row["end_time"]}') - pd.Timestamp(f'{row["date"]} {row["start_time"]}'))
        ).total_seconds(), axis=1)

        df['session_start_time'] = df.groupby('date')['total_time_seconds'].transform('cumsum') - df[
            'total_time_seconds']

        df['session_total_time'] = df.groupby('date')['total_time_seconds'].transform('sum')

        df['percent'] = (df['total_time_seconds'] / df['session_total_time']) * 100
        df['percent'] = df['percent'].round(2).astype(str) + "%"

        df.drop(columns=['total_time_seconds', 'session_start_time', 'session_total_time'], inplace=True)
        return df

#   region New Window entry

    def get_category(self, window_name):
        root = tk.Tk()
        root.withdraw()

        category_window = tk.Toplevel(root)
        category_window.configure(bg=self.theme.windowBg())
        category_window.title("Category Input")

        tk.Label(category_window, text=f"Enter category for '{window_name}':", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "16", "bold")).pack(pady=5)
        
        tk.Label(category_window, text=f"Available categories:", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "10", "bold")).pack(pady=5)


        category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=list(self.CATEGORIES),state="readonly")
        category_dropdown.pack(pady=5)

        tk.Label(category_window, text=f"OR \n Enter manualy:", bg=self.theme.windowBg(), fg="white",
                 font=("Helvetica", "10", "bold")).pack(pady=5)
        
        new_category_entry = tk.Entry(category_window, bg=self.theme.buttonBg(), fg="white")
        new_category_entry.pack(pady=5)

        def submit_category():
            selected_category = category_dropdown.get()
            new_category = new_category_entry.get().strip()

            if selected_category:
                root.category_result = selected_category
                category_window.destroy()
            elif new_category:
                self.CATEGORIES.add(new_category)
                root.category_result = new_category
            else:
                messagebox.showwarning("Warning", "Please select or enter a category.")
                category_window.deiconify()
                return
            category_window.destroy()

        def quit_program():
            root.destroy()

        submit_button = tk.Button(category_window, text="Submit", command=submit_category, bg=self.theme.buttonBg(),
                                  fg="white", font=("Helvetica", "10", "bold"),
                                  activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        submit_button.pack(pady=5)

        # Bind the Enter key to the submit_category function
        new_category_entry.bind("<Return>", lambda event: submit_category())
        category_dropdown.bind("<Return>", lambda event: submit_category())
        submit_button.bind("<Return>", lambda event: submit_category())

        category_window.grab_set()
        category_window.wait_window(category_window)

        return getattr(root, 'category_result', "Misc")