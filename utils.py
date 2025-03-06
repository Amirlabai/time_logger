import os
from tkinter import messagebox

def check_if_file_is_open(csv_file = "time_log.csv"):
    try:
        if os.path.exists(csv_file):
            with open(csv_file, "a"):
                pass
        return True
    except PermissionError:
        messagebox.showerror("File Error",
                             f"The file '{csv_file}' is currently open. Please close it and try again.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return False