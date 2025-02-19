import time
import pandas as pd
import psutil
import win32gui
import win32process
import os
import tkinter as tk
from tkinter import simpledialog, ttk

CSV_FILE = "time_log.csv"
CATEGORIES = set()

def close_existing_csv():
    """Checks if the CSV file is open and attempts to close it."""
    try:
        if os.path.exists(CSV_FILE):
            # Try to open the file in exclusive write mode to check if it's open
            with open(CSV_FILE, "a"): #Try to open in append mode
                pass
        return True # File is not open or was successfully opened

    except PermissionError: # File is open elsewhere
        print(f"The file '{CSV_FILE}' is currently open.")
        return False  # Indicate that the file couldn't be closed
    except Exception as e: # Catch any other exception
        print(f"An error occurred while checking/closing the file: {e}")
        return False


def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process = psutil.Process(pid)
        return process.name().replace(".exe", "")  # Get base program name
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"


def load_existing_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        CATEGORIES.update(df['category'].unique())  # Load existing categories
        return df
    return pd.DataFrame(columns=["date", "window", "category", "start_time", "end_time", "total_time", "percent"])


def get_category(window_name):
    root = tk.Tk()
    root.withdraw()

    while True:
        category_window = tk.Toplevel(root)  # Create a new top-level window
        category_window.title("Category Input")

        category_label = ttk.Label(category_window, text=f"Enter category for '{window_name}':")
        category_label.pack(pady=5)

        category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=list(CATEGORIES))
        category_dropdown.pack(pady=5)

        # Entry for adding a new category
        new_category_entry = ttk.Entry(category_window)
        new_category_entry.pack(pady=5)

        def submit_category():
            selected_category = category_var.get()
            new_category = new_category_entry.get().strip()

            if selected_category:
                category_window.destroy()
                root.category_result = selected_category  # Store the result
            elif new_category:
                CATEGORIES.add(new_category)
                category_window.destroy()
                root.category_result = new_category
            else:
                print("Please select or enter a category.")


        submit_button = ttk.Button(category_window, text="Submit", command=submit_category)
        submit_button.pack(pady=5)

        category_window.grab_set()  # Make the dialog modal
        category_window.wait_window(category_window)  # Wait for the dialog to close

        if hasattr(root, 'category_result'): # Check if result was set
            result = root.category_result
            del root.category_result # Clean up the result
            return result
        else:
            return "misc" # Return a default value or handle cancellation as needed


def calculate_session_percentages(df):
    """Calculates the percentage of time spent in each window for each session."""
    df['date'] = pd.to_datetime(df['date'])  # Ensure date is datetime object
    df['start_time'] = pd.to_datetime(df['start_time'], format='%H:%M:%S').dt.time
    df['end_time'] = pd.to_datetime(df['end_time'], format='%H:%M:%S').dt.time

    df['total_time_seconds'] = df.apply(lambda row: (
        (pd.Timestamp(f'{row["date"]} {row["end_time"]}') - pd.Timestamp(f'{row["date"]} {row["start_time"]}'))
    ).total_seconds(), axis=1)

    df['session_start_time'] = df.groupby('date')['total_time_seconds'].transform('cumsum') - df['total_time_seconds']

    df['session_total_time'] = df.groupby('date')['total_time_seconds'].transform('sum')

    df['percent'] = (df['total_time_seconds'] / df['session_total_time']) * 100
    df['percent'] = df['percent'].round(2).astype(str) + "%"

    df.drop(columns=['total_time_seconds', 'session_start_time', 'session_total_time'], inplace=True)
    return df


def main():
    if not close_existing_csv():
        return

    df = load_existing_data()
    category_map = {row["window"]: row["category"] for _, row in df.iterrows()}
    start_time = time.time()
    session_start = start_time
    active_window = None
    log = []

    try:
        while True:
            new_window = get_active_window()

            if new_window and new_window != active_window:
                if active_window:
                    end_time = time.time()
                    total_time = (end_time - start_time)
                    log.append([time.strftime('%Y-%m-%d'), active_window, category_map[active_window],
                                time.strftime('%H:%M:%S', time.localtime(start_time)),
                                time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time/60,2)])

                if new_window not in category_map:
                    category = get_category(new_window)
                    if category:
                        category_map[new_window] = category
                active_window = new_window
                start_time = time.time()
            if (time.time() - session_start) < 60:
                time_print = time.time() - session_start
                print(f"{int(time_print)} sec")
            elif (time.time() - session_start) < 3600:
                time_print = (time.time() - session_start)/60
                print(f"{round(time_print,2)} minutes")
            elif (time.time() - session_start) > 3600:
                time_print = round(((time.time() - session_start)/3600),4)
                print(f"{time_print} hrs")
            time.sleep(1)
    except KeyboardInterrupt:
        if active_window:
            end_time = time.time()
            total_time = end_time - start_time
            log.append([time.strftime('%Y-%m-%d'), active_window, category_map[active_window],
                        time.strftime('%H:%M:%S', time.localtime(start_time)),
                        time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time/60,2)])

        new_df = pd.DataFrame(log, columns=["date", "window", "category", "start_time", "end_time", "total_time"])
        df = pd.concat([df, new_df], ignore_index=True)

        df = calculate_session_percentages(df) # Calculate percentages after the session
        df.to_csv(CSV_FILE, index=False)
        print("\nSession saved to CSV.")
        os.startfile(CSV_FILE)


if __name__ == "__main__":
    main()
