"""Data layer for time entries and program categories."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils import config
from utils.app_logger import app_logger
from utils.db_utils import get_db_connection


class LoggerService:
    def __init__(self) -> None:
        self.category_map = self._load_program_categories_from_db()
        self.CATEGORIES: set[str] = set()
        for category_value in self.category_map.values():
            if isinstance(category_value, str) and category_value.strip():
                self.CATEGORIES.add(category_value)
        app_logger.info(
            f"LoggerService initialized. Categories loaded from DB: {len(self.CATEGORIES)}"
        )

    def get_CATEGORIES(self) -> list[str]:
        return sorted(self.CATEGORIES)

    def get_program_categories(self) -> dict[str, str]:
        return dict(self.category_map)

    def log_activity(
        self,
        program: str,
        window: str,
        start_time_epoch: float,
        end_time_epoch: float,
        total_time_seconds: float,
    ) -> None:
        current_date_str = time.strftime("%d/%m/%Y", time.localtime(start_time_epoch))
        start_time_str = time.strftime("%H:%M:%S", time.localtime(start_time_epoch))
        end_time_str = time.strftime("%H:%M:%S", time.localtime(end_time_epoch))
        total_time_minutes = round(total_time_seconds / 60, 2)
        category = self.category_map.get(program, "Misc")
        percent_text_placeholder = "0%"

        sql = """
            INSERT INTO time_entries
            (date_text, program_name, window_title, category,
             start_time_text, end_time_text, total_time_minutes,
             start_timestamp_epoch, end_timestamp_epoch, percent_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            current_date_str,
            program,
            window,
            category,
            start_time_str,
            end_time_str,
            total_time_minutes,
            start_time_epoch,
            end_time_epoch,
            percent_text_placeholder,
        )
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    conn.commit()
                    app_logger.debug(
                        f"Activity logged: Prog={program}, Cat={category}, TotalMin={total_time_minutes}"
                    )
                except sqlite3.Error:
                    app_logger.error("Failed to log activity to database", exc_info=True)

    def _load_program_categories_from_db(self) -> dict[str, str]:
        categories: dict[str, str] = {}
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT program_name, category FROM program_categories"
                    )
                    for row in cursor.fetchall():
                        categories[row["program_name"]] = row["category"]
                    app_logger.info(
                        f"Program categories loaded from DB. Count: {len(categories)}"
                    )
                except sqlite3.Error:
                    app_logger.error(
                        "Failed to load program categories from DB", exc_info=True
                    )
        return categories

    def save_program_category_to_db(self, program_name: str, category: str) -> bool:
        sql = (
            "INSERT OR REPLACE INTO program_categories (program_name, category) "
            "VALUES (?, ?)"
        )
        success = False
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, (program_name, category))
                    conn.commit()
                    app_logger.info(
                        f"Program category saved: {program_name} -> {category}"
                    )
                    self.category_map[program_name] = category
                    self.CATEGORIES.add(category)
                    success = True
                except sqlite3.Error:
                    app_logger.error(
                        f"Failed to save program category for '{program_name}'",
                        exc_info=True,
                    )
        return success

    def save_program_categories_batch(
        self, categories: dict[str, str]
    ) -> int:
        saved = 0
        for program_name, category in categories.items():
            if self.save_program_category_to_db(program_name, category):
                saved += 1
        return saved

    def update_categories_in_log_entries(
        self, program_name: str, new_category: str
    ) -> None:
        sql = "UPDATE time_entries SET category = ? WHERE program_name = ?"
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, (new_category, program_name))
                    conn.commit()
                    app_logger.info(
                        f"Updated category to '{new_category}' for '{program_name}'. "
                        f"Rows: {cursor.rowcount}"
                    )
                except sqlite3.Error:
                    app_logger.error(
                        "Failed to update categories in time_entries", exc_info=True
                    )

    def get_all_logged_data(
        self, start_date_str: str | None = None, end_date_str: str | None = None
    ) -> pd.DataFrame:
        app_logger.info(
            f"Fetching logged data. Start: {start_date_str}, End: {end_date_str}"
        )
        query = (
            "SELECT id, date_text, program_name, window_title, category, "
            "start_time_text, end_time_text, total_time_minutes, "
            "start_timestamp_epoch, end_timestamp_epoch, percent_text "
            "FROM time_entries"
        )
        params: list[float] = []
        conditions: list[str] = []
        if start_date_str:
            try:
                start_epoch = datetime.strptime(
                    start_date_str + " 00:00:00", "%d/%m/%Y %H:%M:%S"
                ).timestamp()
                conditions.append("start_timestamp_epoch >= ?")
                params.append(start_epoch)
            except ValueError:
                app_logger.warning(f"Invalid start_date_str: {start_date_str}")
        if end_date_str:
            try:
                end_epoch = datetime.strptime(
                    end_date_str + " 23:59:59", "%d/%m/%Y %H:%M:%S"
                ).timestamp()
                conditions.append("start_timestamp_epoch <= ?")
                params.append(end_epoch)
            except ValueError:
                app_logger.warning(f"Invalid end_date_str: {end_date_str}")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY start_timestamp_epoch ASC"

        with get_db_connection() as conn:
            if conn:
                try:
                    df = pd.read_sql_query(query, conn, params=tuple(params))
                    app_logger.info(f"Fetched {len(df)} log entries.")
                    return df
                except (sqlite3.Error, Exception):
                    app_logger.error("Failed to fetch logged data", exc_info=True)
        return pd.DataFrame()

    def get_category_summary(self) -> list[dict]:
        df = self.get_all_logged_data()
        if df.empty or "category" not in df.columns:
            return []
        category_counts = df["category"].value_counts()
        total = len(df)
        return [
            {
                "category": name,
                "count": int(count),
                "percentage": round((count / total) * 100, 1) if total else 0.0,
            }
            for name, count in category_counts.items()
        ]

    def export_to_csv(
        self,
        file_path: str | Path,
        export_type: str = "all",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
    ) -> None:
        app_logger.info(
            f"Exporting report to {file_path}. Type: {export_type}, "
            f"Start: {start_date_str}, End: {end_date_str}"
        )
        if export_type == "range":
            data_for_report_df = self.get_all_logged_data(start_date_str, end_date_str)
        else:
            data_for_report_df = self.get_all_logged_data()

        if data_for_report_df.empty:
            raise ValueError("No data available for the selected criteria.")

        summary_report_df = data_for_report_df.groupby(
            ["date_text", "category"], as_index=False
        )["total_time_minutes"].sum()
        summary_report_df.to_csv(file_path, index=False)
        app_logger.info(f"Report exported to {file_path}")

    def calculate_session_percentages(self, df_input: pd.DataFrame) -> pd.DataFrame:
        df = df_input.copy()
        if df.empty or "total_time_minutes" not in df.columns:
            df["percent_text"] = "0.00%"
            return df
        if "date_text" not in df.columns:
            df["percent_text"] = "0.00%"
            return df

        df["session_total_time_minutes"] = df.groupby("date_text")[
            "total_time_minutes"
        ].transform("sum")
        df["percent_calc_val"] = 0.0
        non_zero = df["session_total_time_minutes"] != 0
        df.loc[non_zero, "percent_calc_val"] = (
            df.loc[non_zero, "total_time_minutes"]
            / df.loc[non_zero, "session_total_time_minutes"]
        ) * 100
        df["percent_text"] = df["percent_calc_val"].round(2).astype(str) + "%"
        df.drop(
            columns=["session_total_time_minutes", "percent_calc_val"],
            inplace=True,
            errors="ignore",
        )
        return df

    def reload_categories(self) -> None:
        self.category_map = self._load_program_categories_from_db()
        self.CATEGORIES = {
            v for v in self.category_map.values() if isinstance(v, str) and v.strip()
        }
