import time
from logging import exception

import pandas as pd
import psutil
import win32gui
import win32process
import os
import tkinter as tk
from tkinter import simpledialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

CSV_FILE = "time_log.csv"
CATEGORIES = set()

def check_if_file_is_open():
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
    except Exception as e:
        return "Unknown"


def load_existing_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        CATEGORIES.update(df['category'].unique())  # Load existing categories
        return df
    return pd.DataFrame(columns=["date", "window", "category", "start_time", "end_time", "total_time", "percent"])


def get_category(window_name):
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    category_window = tk.Toplevel(root)  # Create a new top-level window
    category_window.title("Category Input")

    ttk.Label(category_window, text=f"Enter category for '{window_name}':").pack(pady=5)

    category_var = tk.StringVar()
    category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=list(CATEGORIES))
    category_dropdown.pack(pady=5)

    new_category_entry = ttk.Entry(category_window)
    new_category_entry.pack(pady=5)

    def submit_category():
        selected_category = category_var.get().strip()
        new_category = new_category_entry.get().strip()

        if selected_category:
            category_window.destroy()
            root.category_result = selected_category  # Store the result
        elif new_category:
            CATEGORIES.add(new_category)  # Add new category
            category_window.destroy()
            root.category_result = new_category
        else:
            print("Please select or enter a category.")

    ttk.Button(category_window, text="Submit", command=submit_category).pack(pady=5)

    category_window.grab_set()  # Make the dialog modal
    category_window.wait_window(category_window)  # Wait for the user to close the window

    result = getattr(root, 'category_result', "Misc")  # Default to "Misc" if nothing is set
    root.destroy()  # Cleanup the hidden root window
    return result



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


def get_time(session_start, new_window, category_map):
    time_frame = int(time.time() - session_start)  # Total elapsed time in seconds

    hours, remainder = divmod(time_frame, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"{new_window} | {category_map[new_window]} | {hours:02}:{minutes:02}:{seconds:02}")

def show_graph(df):
    if df.empty:
        print("No data to display.")
        return

    try:
        # Ensure 'date' column is in datetime format
        df["date"] = pd.to_datetime(df["date"])

        # Filter data for today
        today = pd.Timestamp.today().normalize()
        df_today = df[df["date"] == today]

        if df_today.empty:
            print("No data for today.")
            return

        # Total time calculations
        total_time_all = df["total_time"].sum()  # Total time across all data
        total_time_today = df_today["total_time"].sum()  # Today's total time

        # Group by category and compute percentages
        category_time_today = df_today.groupby("category")["total_time"].sum()
        category_time_all = df.groupby("category")["total_time"].sum()

        category_percentage_today = (category_time_today / total_time_today) * 100
        category_percentage_all = (category_time_all / total_time_all) * 100

        # Align categories (fill missing categories with 0%)
        all_categories = set(category_percentage_today.index) | set(category_percentage_all.index)
        category_percentage_today = category_percentage_today.reindex(all_categories, fill_value=0)
        category_percentage_all = category_percentage_all.reindex(all_categories, fill_value=0)

        # Sort by today's highest percentage for better visualization
        category_percentage_today = category_percentage_today.sort_values(ascending=False)
        category_percentage_all = category_percentage_all[category_percentage_today.index]

        # Create a new Tkinter window
        graph_window = tk.Toplevel()
        graph_window.title("Category Percentage Comparison")

        # Create figure and canvas
        fig, ax = plt.subplots(figsize=(12, 6))
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack()

        # Bar width
        bar_width = 0.4
        x_labels = list(category_percentage_today.index)
        x_positions = range(len(x_labels))

        # Plot both today's and overall percentages
        ax.bar(x_positions, category_percentage_today, width=bar_width, label="Today", color='skyblue')
        ax.bar([x + bar_width for x in x_positions], category_percentage_all, width=bar_width, label="Overall", color='orange')

        # Add values on top of today's bars
        for i, v in enumerate(category_percentage_today):
            ax.text(x_positions[i], v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold')

        # Add values on top of overall bars
        for i, v in enumerate(category_percentage_all):
            ax.text(x_positions[i] + bar_width, v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold')

        # Labels and formatting
        ax.set_ylabel("Percentage (%)")
        ax.set_xlabel("Categories")
        ax.set_title("Category Percentage (Today vs Overall)")
        ax.set_xticks([x + bar_width / 2 for x in x_positions])
        ax.set_xticklabels(x_labels, rotation=25, ha="right", fontsize=10)
        ax.legend()

        fig.tight_layout()
        canvas.draw()

        # Close button
        def close_graph():
            graph_window.destroy()
            show_graph.is_open = False

        close_button = ttk.Button(graph_window, text="Close", command=close_graph)
        close_button.pack(pady=5)

        show_graph.is_open = True

    except Exception as e:
        print(f"Error showing graph: {e}")

show_graph.is_open = False # Initialize the flag

def main():
    if not check_if_file_is_open():
        return

    df = load_existing_data()
    category_map = {row["window"]: row["category"] for _, row in df.iterrows()}
    start_time = time.time()
    session_start = start_time
    active_window = None
    log = []

    root = tk.Tk()  # Create the root window (important!)
    root.withdraw()  # Hide the root window

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
            get_time(session_start, new_window, category_map)
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
        #os.startfile(CSV_FILE)
        show_graph(df)
        root.mainloop()
        while show_graph.is_open:  # Keep the main thread alive until the graph window is closed
            time.sleep(0.1)  # Check the flag periodically
        print("Exiting...")
        root.destroy()


if __name__ == "__main__":
    main()

