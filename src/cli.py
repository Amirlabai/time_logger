"""Headless utilities for database init and export."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    src_dir = Path(__file__).resolve().parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> None:
    _ensure_src_on_path()
    from utils import config
    from utils.core_functions import migrate_legacy_data_if_needed
    from utils.db_utils import initialize_database
    from models.logger_service import LoggerService

    parser = argparse.ArgumentParser(description="Time Tracker CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Initialize SQLite database")

    export_parser = sub.add_parser("export", help="Export activity report to CSV")
    export_parser.add_argument("path", help="Output CSV path")
    export_parser.add_argument("--type", choices=["all", "range"], default="all")
    export_parser.add_argument("--start", help="Start date DD/MM/YYYY")
    export_parser.add_argument("--end", help="End date DD/MM/YYYY")

    args = parser.parse_args()
    migrate_legacy_data_if_needed(
        config.LEGACY_DATABASE_FILE_PATH,
        config.DATABASE_FILE_PATH,
    )
    config.ensure_directories_exist()
    initialize_database()
    logger = LoggerService()

    if args.command == "init-db":
        print(f"Database ready at {config.DATABASE_FILE_PATH}")
    elif args.command == "export":
        logger.export_to_csv(args.path, args.type, args.start, args.end)
        print(f"Exported to {args.path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
