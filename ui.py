import tkinter as tk
from tkinter import ttk, messagebox
import time


class TimeTrackerUI:
    def __init__(self, root, tracker, graph_display, theme, logger):
        self.root = root
        self.tracker = tracker
        self.graph_display = graph_display
        self.theme = theme
        self.logger = logger
        self.setup_ui()

#   region initiate GUI

    def setup_ui(self):
        self.root.configure(bg=self.theme.windowBg())
        self.root.title("Time Tracker")
        self.root.minsize(width=400, height=350)
        self.root.iconbitmap("icons\\timer_icon_32.ico")
        self.root.withdraw()

        categories_label = tk.Label(self.root, text="Available Categories:", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "16", "bold"))
        categories_label.pack(pady=10)

        self.categories_listbox = tk.Listbox(self.root, height=5, bg=self.theme.buttonBg(), fg="white")
        self.categories_listbox.pack()
        self.update_category_list()

        categories_discription = tk.Label(self.root, text="Category entry: name (count) | percentage", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "8"))
        categories_discription.pack()

        self.running_time_label = tk.Label(self.root, text="Running Time: 00:00:00", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold"))
        self.running_time_label.pack(pady=5)

        self.current_window_label = tk.Label(self.root, text="Current Window: None", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold"))
        self.current_window_label.pack(pady=5)

        def change_time_window():
            top_change_time_window = tk.Toplevel(self.root)
            top_change_time_window.title("Enter break time window")
            time_window_entry = ttk.Entry(top_change_time_window)
            time_window_entry.pack()
            self.tracker.break_time = time_window_entry.get()

        break_timer_frame = tk.Frame(self.root, bg=self.theme.windowBg())
        break_timer_frame.pack(pady=(10, 5))

        change_time_window_button = tk.Button(break_timer_frame, text="Change Window Time", command=change_time_window, bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        change_time_window_button.grid(row=0,column=0)
        
        self.time_for_break = tk.Label(break_timer_frame, text=f" time Window: {self.tracker.break_time}", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold"))
        self.time_for_break.grid(row=0,column=1)

        self.break_timer = tk.Label(break_timer_frame, text=f"Time untill break: {self.tracker.break_time_counter}", bg=self.theme.windowBg(), fg="white", font=("Helvetica", "12", "bold"))
        self.break_timer.grid(row=1,column=0,columnspan=2)

        button_frame = tk.Frame(self.root, bg=self.theme.buttonBg())
        button_frame.pack(pady=(10, 5))

        graph_button = tk.Button(button_frame, text="Show Graph", command=self.get_graph, bg=self.theme.buttonBg(), fg="white", font=("Helvetica", "10", "bold"),
                                 activebackground=self.theme.activeButtonBg(), activeforeground="white", borderwidth=2)
        graph_button.pack()

        close_button = tk.Button(self.root, text="Close Time Tracker", command=self.close_program, bg=self.theme.closeButtonBg(), fg="white", font=("Helvetica", "10", "bold"),
                               activebackground=self.theme.closeActiveButtonBg(), activeforeground="white", borderwidth=2)
        close_button.pack(pady=(5, 10))

        self.root.after(100, lambda: self.root.deiconify())
        self.update_running_time()

#   region update GUI

    def update_category_list(self):
        self.categories_listbox.delete(0, tk.END)
        category_counts = self.logger.df['category'].value_counts()
        total_counts = self.logger.df.shape[0]
        for category, count in category_counts.items():
            self.categories_listbox.insert(tk.END, f"{category} ({count}) | {round((count/total_counts)*100,2)}%")

    def update_running_time(self):
        time_frame = int(time.time() - self.tracker.start_time)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.running_time_label.config(text=f"Current program Running Time: {hours:02}:{minutes:02}:{seconds:02}")
        try:

            self.current_window_label.config(text=f"Previous Window: {self.tracker.perv_window or 'None'} | {self.tracker.total_time/60:.2f} minutes")

        except:
            self.current_window_label.config(text=f"Current window: {self.tracker.active_window or 'None'}")
        
        self.break_timer.config(text=f"Time untill break: {self.tracker.break_time_counter}")

        self.root.after(1000, self.update_running_time)

#   region Buttons

    def get_graph(self):
        if self.graph_display.is_open:
                graph_window = [w for w in tk.Toplevel.winfo_children(self.root) if isinstance(w, tk.Toplevel)][0]
                graph_window.destroy()
                self.graph_display.is_open = False
        self.graph_display.show_graph(self.logger.df)

    def close_program(self):
        self.tracker.stop_tracking()
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to close the program?"):
            #time.sleep(1)
            if self.graph_display.is_open:
                graph_window = [w for w in tk.Toplevel.winfo_children(self.root) if isinstance(w, tk.Toplevel)][0]
                graph_window.destroy()
                self.graph_display.is_open = False
            self.root.destroy()
            self.root.quit()