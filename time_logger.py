import time
import pandas as pd
import psutil
import win32gui
import win32process
import os
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import traceback
from PIL import Image, ImageTk
import threading

CSV_FILE = "time_log.csv"
CATEGORIES = set()


def get_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb

windowBg = get_rgb((30, 30, 30))
buttonBg = get_rgb((50, 50, 50))
activeButtonBg = get_rgb((25, 35, 50))

def check_if_file_is_open():
    try:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "a"):
                pass
        return True
    except PermissionError:
        messagebox.showerror("File Error", f"The file '{CSV_FILE}' is currently open. Please close it and try again.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return False


def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().replace(".exe", "")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"
    except Exception:
        return "Unknown"


def load_existing_data():
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            CATEGORIES.update(df['category'].unique())
            return df
        return pd.DataFrame(columns=["date", "window", "category", "start_time", "end_time", "total_time", "percent"])
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["date", "window", "category", "start_time", "end_time", "total_time", "percent"])
    except Exception as e:
        messagebox.showerror("Error Loading Data", f"Error loading data: {e}")
        return pd.DataFrame(columns=["date", "window", "category", "start_time", "end_time", "total_time", "percent"])


def get_category(window_name):
    root = tk.Tk()
    root.withdraw()

    category_window = tk.Toplevel(root)
    category_window.configure(bg=windowBg)
    category_window.title("Category Input")

    tk.Label(category_window, text=f"Enter category for '{window_name}':",bg=windowBg,fg="white",font=("Arial", "10", "bold") ).pack(pady=5)

    category_var = tk.StringVar()
    category_dropdown = ttk.Combobox(category_window, textvariable=category_var, values=list(CATEGORIES))
    category_dropdown.pack(pady=5)

    new_category_entry = tk.Entry(category_window,bg=buttonBg,fg="white")
    new_category_entry.pack(pady=5)

    def submit_category():
        selected_category = category_dropdown.get()
        new_category = new_category_entry.get().strip()

        if selected_category:
            root.category_result = selected_category
            category_window.destroy()
        elif new_category:
            CATEGORIES.add(new_category)
            root.category_result = new_category
        else:
            messagebox.showwarning("Warning", "Please select or enter a category.")
            category_window.deiconify()
            return
        category_window.destroy()

    def quit_program():
        root.destroy()

    tk.Button(category_window, text="Submit", command=submit_category, bg=windowBg,fg="white",font=("Arial", "10", "bold"),
              activebackground=activeButtonBg, activeforeground="white", borderwidth=2).pack(pady=5)

    category_window.grab_set()
    category_window.wait_window(category_window)

    return getattr(root, 'category_result', "Misc")


def calculate_session_percentages(df):
    if df.empty:
        return df

    df['date'] = pd.to_datetime(df['date'])
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
    windowBg = get_rgb((30, 30, 30))
    buttonBg = get_rgb((50, 50, 50))
    activeButtonBg = get_rgb((25, 35, 50))
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

        # Calculate total days
        total_days = df["date"].nunique()

        # Calculate total study hours
        df["date"] = pd.to_datetime(df["date"])  # Make sure 'date' is datetime
        df_study = df[df["category"] == "study"]  # Filter for 'study' category
        total_study_hours = df_study["total_time"].sum() if not df_study.empty else 0  # Handle case where no study data
        total_study_hours = total_study_hours / 60  # converet to hours

        # Calculate productivity (using total study hours)
        if total_days * 24 > 0:
            productivity = (total_study_hours / (
                        total_days * 24 * (2 / 3))) * 100 if total_study_hours > 0 else 0  # Handle 0 study hours
        else:
            productivity = 0

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
        graph_window.configure(bg=windowBg)
        graph_window.title("Category Percentage Comparison")

        # Display information at the top
        info_frame = tk.Frame(graph_window, bg=buttonBg)
        #info_frame = tk.Frame(graph_window)
        info_frame.pack(pady=(5, 5))

        info_label = tk.Label(info_frame,
                               text=f"Today Session: {round(total_time_today/60,2)} | Total Days: {total_days} | Total Study Hours: {total_study_hours:.2f} | Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)",
                               font=("Helvetica", 12),bg=windowBg,fg="white")
        info_label.pack()

        # Create figure and canvas
        fig, ax = plt.subplots(figsize=(12, 6),facecolor=buttonBg)
        #plt.figure(facecolor=windowBg)
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
            ax.text(x_positions[i], v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold',color="white")

        # Add values on top of overall bars
        for i, v in enumerate(category_percentage_all):
            ax.text(x_positions[i] + bar_width, v + 1, f"{v:.1f}%", ha='center', fontsize=10, fontweight='bold',color="white")

        # Labels and formatting
        ax.set_facecolor(windowBg)
        ax.set_ylabel("Percentage (%)",color="white")
        ax.set_xlabel("Categories",color="white")
        ax.set_title("Category Percentage (Today vs Overall)",fontweight='bold',color="white")
        ax.set_xticks([x + bar_width / 2 for x in x_positions])
        ax.set_xticklabels(x_labels, rotation=25, ha="right", fontsize=10,color="white")
        ax.tick_params(axis='y', colors='white')
        ax.yaxis.label.set_color('white')  # ensure y axis label is white
        ax.xaxis.label.set_color('white')
        ax.legend()

        fig.tight_layout()
        canvas.draw()

        # Close button
        def close_graph():
            graph_window.destroy()
            show_graph.is_open = False

        close_button = tk.Button(graph_window, text="Close", command=close_graph, bg=buttonBg, fg="white", font=("Arial", "10", "bold"),
                             activebackground=activeButtonBg, activeforeground="white", borderwidth=2)
        close_button.pack(pady=5)

        show_graph.is_open = True

    except Exception as e:
        print(f"Error showing graph: {e}")


show_graph.is_open = False  # Initialize the flag


def main():
    windowBg = get_rgb((30, 30, 30))
    buttonBg = get_rgb((50, 50, 50))
    activeButtonBg = get_rgb((25, 35, 50))

    if not check_if_file_is_open():
        return

    start_time = time.time()
    session_start = start_time
    total_time = 0
    active_window = None
    perv_window = None

    root = tk.Tk()  # Create Tk window
    root.configure(bg=windowBg)
    # Set minimum width and height
    root.minsize(width=300, height=200)  # Adjust values as needed

    root.title("Time Tracker")
    root.withdraw()  # Hide the main window initially

    # Tkinter window elements
    categories_label = tk.Label(root, text="Available Categories:", bg=windowBg, fg="white",font=("Arial", "16", "bold"))
    categories_label.pack(pady=5)

    categories_listbox = tk.Listbox(root, height=5)
    categories_listbox.pack(pady=5)

    running_time_label = tk.Label(root, text="Running Time: 00:00:00", bg=windowBg, fg="white",font=("Arial", "12", "bold"))
    running_time_label.pack(pady=5)

    current_window_label = tk.Label(root, text="Current Window: None", bg=windowBg, fg="white",font=("Arial", "12", "bold"))
    current_window_label.pack(pady=5)

    def update_running_time():
        nonlocal session_start, perv_window, active_window
        time_frame = int(time.time() - session_start)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        running_time_label.config(text=f"Program Running Time: {hours:02}:{minutes:02}:{seconds:02}")
        try:
            current_window_label.config(text=f"Current Window: {perv_window or 'None'}")  # Update current window
        except:
            current_window_label.config(text=f"Current Window: {active_window or 'None'}")  # Update current window
        root.after(1000, update_running_time)

    update_running_time()

    df = load_existing_data()  # Load data after creating the Tk window

    # Calculate counts of unique categories
    category_counts = df['category'].value_counts()

    for category, count in category_counts.items():
        categories_listbox.insert(tk.END, f"{category} ({count})")  # Format with count

    category_map = {row["window"]: row["category"] for _, row in df.iterrows()}

    running = True  # Flag to control the main loop

    log = []

    def get_graph():
        nonlocal df, log
        if active_window:
            end_time = time.time()
            total_time = end_time - start_time
            log.append([time.strftime('%Y-%m-%d'), active_window, category_map.get(active_window, "Misc"),
                        time.strftime('%H:%M:%S', time.localtime(start_time)),
                        time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time / 60, 2)])

        new_df = pd.DataFrame(log, columns=["date", "window", "category", "start_time", "end_time", "total_time"])
        df = pd.concat([df, new_df], ignore_index=True)
        df = calculate_session_percentages(df)
        log = []
        show_graph(df)



    def close_program():
        nonlocal running, active_window, start_time, log, df
        if active_window:
            end_time = time.time()
            total_time = end_time - start_time
            log.append([time.strftime('%Y-%m-%d'), active_window, category_map.get(active_window, "Misc"),
                        time.strftime('%H:%M:%S', time.localtime(start_time)),
                        time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time / 60, 2)])

        new_df = pd.DataFrame(log, columns=["date", "window", "category", "start_time", "end_time", "total_time"])
        df = pd.concat([df, new_df], ignore_index=True)
        df = calculate_session_percentages(df)
        df.to_csv(CSV_FILE, index=False)

        if messagebox.askyesno("Confirm Exit", "Are you sure you want to close the program?"):  # Confirmation dialog
            if show_graph.is_open:  # Check if the graph window is still open
                graph_window = [w for w in tk.Toplevel.winfo_children(root) if isinstance(w, tk.Toplevel)][
                    0]  # Get the graph window
                graph_window.destroy()  # Close the graph window
                show_graph.is_open = False
            running = False
            root.destroy()
            root.quit()

    # Frame for the first two buttons to allow centering
    button_frame = tk.Frame(root,bg=buttonBg)
    button_frame.pack(pady=(10, 5))  # Add some padding around the frame

    graph_button = tk.Button(button_frame, text="Show Graph", command=get_graph, bg=buttonBg, fg="white", font=("Arial", "10", "bold"),
                             activebackground=activeButtonBg, activeforeground="white", borderwidth=2)
    graph_button.pack()

    close_button = tk.Button(root, text="Close Time Tracker", command=close_program, bg=get_rgb((200,30,30)), fg="white", font=("Arial", "10", "bold"),
                           activebackground=get_rgb((100,50,50)), activeforeground="white", borderwidth=2)
    close_button.pack(pady=(5, 10))

    root.after(100, lambda: root.deiconify())

    def window_tracker():  # Function for the separate thread
        nonlocal running, active_window, start_time, log, category_map, perv_window
        try:
            while running:
                new_window = get_active_window()

                if new_window and new_window != active_window:
                    if active_window:
                        perv_window = active_window
                        end_time = time.time()
                        total_time = (end_time - start_time)
                        log.append([time.strftime('%Y-%m-%d'), active_window, category_map.get(active_window, "Misc"),
                                    time.strftime('%H:%M:%S', time.localtime(start_time)),
                                    time.strftime('%H:%M:%S', time.localtime(end_time)), round(total_time / 60, 2)])

                    if new_window not in category_map:
                        category = get_category(new_window)
                        if category:
                            category_map[new_window] = category
                    perv_window = active_window
                    active_window = new_window
                    start_time = time.time()
                time.sleep(1)
        except Exception as e:
            print(f"Error in window_tracker thread: {e}")
            traceback.print_exc()

    thread = threading.Thread(target=window_tracker)  # Create the thread
    thread.daemon = True  # Allow the main thread to exit even if this thread is running
    thread.start()  # Start the thread

    root.mainloop()  # Mainloop is here and it runs concurrently with the thread


if __name__ == "__main__":
    main()
