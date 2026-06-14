"""Graph data preparation — JSON payloads for Chart.js."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from utils.app_logger import app_logger
from models.logger_service import LoggerService


CHART_COLORS = [
    "#87CEEB",
    "#FFA500",
    "#90EE90",
    "#FFB6C1",
    "#DDA0DD",
    "#F0E68C",
    "#20B2AA",
    "#FF6347",
]


def format_time_display(total_minutes: float) -> str:
    if pd.isna(total_minutes) or total_minutes == 0:
        return "0 minutes"
    if total_minutes < 1:
        return f"{total_minutes * 60:.0f} seconds"
    if total_minutes < 60:
        return f"{total_minutes:.1f} minutes"
    return f"{total_minutes / 60:.2f} hours"


class GraphService:
    def __init__(self, logger_service: LoggerService) -> None:
        self.logger = logger_service

    def _fetch_and_prepare_data(
        self,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        df_all_entries = self.logger.get_all_logged_data()
        if df_all_entries.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        df_all_entries["total_time_minutes"] = pd.to_numeric(
            df_all_entries["total_time_minutes"], errors="coerce"
        ).fillna(0)
        df_all_entries["parsed_date"] = pd.to_datetime(
            df_all_entries["date_text"], format="%d/%m/%Y", errors="coerce"
        )
        df_all_entries.dropna(subset=["parsed_date"], inplace=True)

        if df_all_entries.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        today_dt = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        current_month_start = today_dt.replace(day=1)

        df_today = df_all_entries[df_all_entries["parsed_date"] == today_dt].copy()
        df_this_month = df_all_entries[
            df_all_entries["parsed_date"] >= current_month_start
        ].copy()
        return df_today, df_this_month, df_all_entries

    def get_top_ten_programs(self, df_source: pd.DataFrame) -> list[dict]:
        if (
            df_source.empty
            or "program_name" not in df_source.columns
            or "total_time_minutes" not in df_source.columns
        ):
            return []
        try:
            value_counts = df_source.groupby(["program_name", "category"])[
                "total_time_minutes"
            ].sum()
            top_10 = value_counts.nlargest(10).reset_index(name="total_minutes")
            return [
                {
                    "program_name": str(row["program_name"])[:25],
                    "category": str(row["category"])[:15],
                    "time_display": format_time_display(row["total_minutes"]),
                    "total_minutes": float(row["total_minutes"]),
                }
                for _, row in top_10.iterrows()
            ]
        except KeyError:
            app_logger.error("KeyError in get_top_ten_programs", exc_info=True)
            return []

    def _compute_stats(
        self,
        df_today: pd.DataFrame,
        df_this_month: pd.DataFrame,
        df_overall: pd.DataFrame,
        selected_cat: str,
    ) -> dict[str, Any]:
        if selected_cat != "All Categories":
            df_today_stat = df_today[df_today["category"] == selected_cat]
            df_month_stat = df_this_month[df_this_month["category"] == selected_cat]
            df_overall_stat = df_overall[df_overall["category"] == selected_cat]
            cat_display_name = selected_cat
        else:
            df_today_stat = df_today[df_today["category"] != "Break"]
            df_month_stat = df_this_month[df_this_month["category"] != "Break"]
            df_overall_stat = df_overall[df_overall["category"] != "Break"]
            cat_display_name = "Productive"

        time_today = float(df_today_stat["total_time_minutes"].sum())
        time_month = float(df_month_stat["total_time_minutes"].sum())
        days_month = int(df_month_stat["parsed_date"].nunique()) if not df_month_stat.empty else 0
        time_overall = float(df_overall_stat["total_time_minutes"].sum())
        days_overall = (
            int(df_overall_stat["parsed_date"].nunique())
            if not df_overall_stat.empty
            else 0
        )

        prod_month = (
            ((time_month / 60) / (days_month * 16) * 100)
            if days_month > 0 and time_month > 0
            else 0
        )
        prod_overall = (
            ((time_overall / 60) / (days_overall * 16) * 100)
            if days_overall > 0 and time_overall > 0
            else 0
        )

        return {
            "display_name": cat_display_name,
            "today": format_time_display(time_today),
            "month": format_time_display(time_month),
            "month_days": days_month,
            "month_productivity": round(prod_month, 1),
            "overall": format_time_display(time_overall),
            "overall_days": days_overall,
            "overall_productivity": round(prod_overall, 1),
        }

    def get_graph_data(self, filter_category: str = "All Categories") -> dict:
        df_today, df_this_month, df_overall = self._fetch_and_prepare_data()
        if df_overall.empty:
            return {"status": "error", "message": "No data available to display."}

        stats = self._compute_stats(
            df_today, df_this_month, df_overall, filter_category
        )

        total_time_today = df_today["total_time_minutes"].sum()
        cat_time_today = df_today.groupby("category")["total_time_minutes"].sum()
        cat_perc_today = (
            (cat_time_today / total_time_today * 100)
            if total_time_today > 0
            else pd.Series(dtype="float64")
        )

        total_time_overall = df_overall["total_time_minutes"].sum()
        cat_time_overall = df_overall.groupby("category")["total_time_minutes"].sum()
        cat_perc_overall = (
            (cat_time_overall / total_time_overall * 100)
            if total_time_overall > 0
            else pd.Series(dtype="float64")
        )

        all_categories = sorted(
            set(cat_perc_today.index) | set(cat_perc_overall.index)
        )
        cat_perc_today = cat_perc_today.reindex(all_categories, fill_value=0)
        cat_perc_overall = cat_perc_overall.reindex(all_categories, fill_value=0)

        colors = [
            CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(all_categories))
        ]

        available_categories = ["All Categories"] + self.logger.get_CATEGORIES()

        return {
            "status": "success",
            "stats": stats,
            "top_programs": self.get_top_ten_programs(df_overall),
            "available_categories": available_categories,
            "chart": {
                "labels": list(all_categories),
                "today_values": [round(float(v), 1) for v in cat_perc_today],
                "overall_values": [round(float(v), 1) for v in cat_perc_overall],
                "colors": colors,
            },
        }
