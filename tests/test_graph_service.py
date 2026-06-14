"""Tests for graph JSON payloads."""

import pandas as pd

from models.graph_service import GraphService, format_time_display


class StubLogger:
    def get_all_logged_data(self):
        return pd.DataFrame(
            [
                {
                    "date_text": "01/06/2026",
                    "program_name": "code",
                    "category": "Dev",
                    "total_time_minutes": 60,
                },
                {
                    "date_text": "01/06/2026",
                    "program_name": "browser",
                    "category": "Web",
                    "total_time_minutes": 30,
                },
            ]
        )

    def get_CATEGORIES(self):
        return ["Dev", "Web"]


def test_format_time_display():
    assert format_time_display(0) == "0 minutes"
    assert "minute" in format_time_display(45)


def test_get_graph_data_shape():
    service = GraphService(StubLogger())
    result = service.get_graph_data("All Categories")
    assert result["status"] == "success"
    assert "chart" in result
    assert "labels" in result["chart"]
    assert "today_values" in result["chart"]
    assert isinstance(result["top_programs"], list)
