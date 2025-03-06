import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class GraphDisplay:
    def __init__(self, logger, theme):
        self.logger = logger
        self.theme = theme
        self.is_open = False

    def show_graph(self, df):
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

            total_time_all = df["total_time"].sum()
            total_time_today = df_today["total_time"].sum()
            total_days = df["date"].nunique()
            df_study = df[df["category"] == "study"]
            total_study_hours = df_study["total_time"].sum() if not df_study.empty else 0
            total_study_hours = total_study_hours / 60
            productivity = (total_study_hours / (total_days * 24 * (2 / 3))) * 100 if total_study_hours > 0 and total_days * 24 > 0 else 0

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
            graph_window.configure(bg=self.theme.windowBg())
            graph_window.title("Category Percentage Comparison")

            info_frame = tk.Frame(graph_window, bg=self.theme.buttonBg())
            info_frame.pack(pady=(5, 5))

            info_label = tk.Label(info_frame,
                                   text=f"Today Session: {round(total_time_today/60,2)} | Total Days: {total_days} | Total Study Hours: {total_study_hours:.2f} | Productivity: {productivity:.1f}% (Assuming 8 hours sleep zZzZ)",
                                   font=("Helvetica", 12), bg=self.theme.windowBg(), fg="white")
            info_label.pack()

            fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.theme.buttonBg())
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.get_tk_widget().pack()

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