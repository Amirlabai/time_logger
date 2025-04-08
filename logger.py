import pandas as pd
import time
import os
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from themes import Theme
import datetime
import json

class Logger:
    def __init__(self, csv_file,theme):
        self.csv_file = csv_file
        self.theme = Theme()
        self.df = self.load_existing_data()
        self.category_map = self.load_dict_from_txt()
        self.log = []
        self.CATEGORIES = set(self.category_map.values())

    def get_CATEGORIES(self):
        return self.CATEGORIES

    def load_existing_data(self):
        try:
            if os.path.exists(self.csv_file):

                df = pd.read_csv(self.csv_file, dayfirst=True)
                #print(f"import data frame \n{df.head()}")
                #df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors='coerce')

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
        #print(f"log activity data frame \n{self.df.head()}")
        self.log.append([time.strftime('%d/%m/%Y'),program, window, self.category_map.get(program, "Misc"),
                         time.strftime('%H:%M:%S', time.localtime(start_time)),
                         time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time / 60, 2),0])
        self.save_log_to_csv()

    def save_log_to_csv(self):
        #self.df["date"] = pd.to_datetime(self.df["date"]).dt.strftime("%d/%m/%Y")
        print(f"\nsave log data frame \n\n{self.df.head(1)} \n\n {self.df.tail(1)} \n\n{self.log}\n")
        try:
            now = datetime.datetime.now()
            print(f"{now.day}/{now.month}/{now.year}")
            df_date = self.df.iloc[0,0]
            df_date = datetime.datetime.strptime(df_date,'%d/%m/%Y').date()
            print(f"{df_date.day}/{df_date.month}/{df_date.year}")
            log_date = self.log[0][0]
            log_date = datetime.datetime.strptime(log_date, '%d/%m/%Y').date()
            print(f"{log_date.day}/{log_date.month}/{log_date.year}")

            '''try:
                df_date = str(self.df.iloc[0,0]).split("-")[1]
            except:
                df_date = str(self.df.iloc[0,0]).split("/")[1]
            try:
                log_date = self.log[0][0].split("-")[1]
            except:
                log_date = self.log[0][0].split("/")[1]
            #print(df_work_hours)'''

            if df_date.month != log_date.month:
                df_work_hours = self.df.groupby(['date', 'category'])['total_time'].sum()
                df_work_hours.to_csv(f"C:\\timeLog\\report\\report_{now.year}{now.month-1}_{now.hour}{now.minute}{now.second}.csv", index=False)
                self.df.to_csv(f"C:\\timeLog\\log\\log_{now.year}{now.month-1}_{now.hour}{now.minute}{now.second}.csv", index=False)
                new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
                new_df = self.calculate_session_percentages(new_df)
                new_df.to_csv(self.csv_file, index=False,date_format='%d/%m/%Y')
                self.log = []
                self.df = self.load_existing_data()

            else:
                new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                self.df = self.calculate_session_percentages(self.df)
                self.df.to_csv(self.csv_file, index=False,date_format='%d/%m/%Y')
                self.log = []
        except:
            new_df = pd.DataFrame(self.log, columns=["date", "program", "window", "category", "start_time", "end_time", "total_time", "percent"])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df = self.calculate_session_percentages(self.df)
            self.df.to_csv(self.csv_file, index=False,date_format='%d/%m/%Y')
            #print(self.log)
            self.log = []

    def calculate_session_percentages(self, df):
        if df.empty:
            return df

        #df['date'] = pd.to_datetime(df['date'], format="%d/%m/%Y")

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
                self.category_map[window_name] = selected_category
                category_window.destroy()
            elif new_category:
                self.CATEGORIES.add(new_category)
                self.category_map[window_name] = new_category
                self.save_dict_to_txt()
                root.category_result = new_category.title()
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
    
    def save_dict_to_txt(self):
        """Save dictionary to a text file in JSON format."""
        with open('user_programs.txt', "w") as file:
            json.dump(self.category_map, file, indent=4)

    def load_dict_from_txt(self):
        """Load dictionary from the text file if it exists, otherwise return an empty dict."""
        if os.path.exists('user_programs.txt') and os.path.getsize('user_programs.txt') > 0:
            with open('user_programs.txt', "r") as file:
                return json.load(file)
        return {}  # Return empty dictionary if file does not exist or is empty