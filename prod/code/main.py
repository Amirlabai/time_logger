"""This entry point is deprecated. Use src/web_app.py instead."""

import sys


def main() -> None:
    print("Time Tracker now uses PyWebView. Run:")
    print("  python src/web_app.py")
    print("Or after install: time-tracker")
    sys.exit(0)


if __name__ == "__main__":
    main()
