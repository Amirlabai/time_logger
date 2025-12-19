# Time Tracker

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md) The Time Tracker is a Python application designed to monitor application usage on your computer, categorize the time spent, and provide insights through logs, graphs, and reports.

## Table of Contents

* [Features](#features)
* [Technical Stack](#technical-stack)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
* [Data Storage](#data-storage)
* [Architecture & Thread Safety](#architecture--thread-safety)
* [Usage](#usage)
    * [Automatic Tracking](#automatic-tracking)
    * [Categorization](#categorization)
    * [Break Timer](#break-timer)
    * [Viewing Graphs](#viewing-graphs)
    * [Exporting Reports](#exporting-reports)
* [Known Issues](#known-issues)
* [Contributing](#contributing)
* [License](#license)

## Features

* **Automatic Window Detection:** Monitors the currently active window and associated application.
* **Dynamic Category Assignment:**
    * Prompts users to assign categories to newly detected applications (thread-safe dialog system).
    * Remembers categories for future use, stored in SQLite database.
    * Provides a UI to edit program-to-category mappings with bulk update support.
* **Detailed Time Logging:** Records start time, end time, and duration for each application window session.
* **Session-Based Percentage Calculation:** Calculates the percentage of time spent in each application per day.
* **SQLite Database Storage:**
    * All time entries stored in SQLite database (`time_tracker_data.sqlite`) for reliable, fast access.
    * Automatic database initialization and schema management.
    * Indexed queries for efficient data retrieval.
    * Export functionality to CSV for reports and archival.
* **Activity Report Export:** UI option to export summarized activity (total time per category per day) as a CSV file, supporting export of all data or a specific date range.
* **Graphical Usage Insights:**
    * Displays bar charts comparing "Today" vs. "Overall" time percentage per category.
    * Shows productivity statistics (Today, This Month, Overall).
    * Lists the top ten most used programs.
* **Configurable Break Timer:**
    * Visual countdown timer with a pop-up alert for break reminders.
    * Break interval is configurable via the UI (default 50 mins, min 10 mins).
    * Supports pause, resume, and reset functionalities.
* **Robust Logging & Error Handling:**
    * Comprehensive application event logging to console and a rotating file (`time_tracker_app.log`).
    * Attempts to handle file access issues gracefully.
    * Thread-safe database operations with proper connection management.
* **Thread-Safe Architecture:**
    * Queue-based communication between background tracking thread and GUI.
    * All GUI operations safely executed on the main thread.
    * Prevents crashes and race conditions from multi-threaded access.
* **Theming:** Basic UI theming for a consistent look and feel.

## Technical Stack

* **Language:** Python 3
* **Core Libraries:**
    * `Tkinter` for the GUI.
    * `sqlite3` for database storage (Python standard library).
    * `pandas` for data manipulation and CSV export.
    * `psutil` for process information.
    * `pywin32` for Windows-specific API interactions (active window detection).
    * `matplotlib` for generating graphs.
* **Database:** SQLite for persistent storage of time entries and program categories.
* **Operating System:** Currently Windows-specific due to `pywin32` usage for window tracking.

## Prerequisites

* Python 3.x installed.
* Access to a command line/terminal.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd time-tracker # Or your repository's directory name
    ```

2.  **Create a Project Root Marker (if needed):**
    The application uses a marker file named `.project_root` in the base project directory to correctly determine paths. Ensure this empty file exists in the root of your cloned repository if `config.py` relies on it and it's not committed.
    ```bash
    # In the project root directory
    touch .project_root # For Linux/macOS
    # type nul > .project_root # For Windows CMD
    # New-Item .project_root -ItemType File # For Windows PowerShell
    ```
    *Note: The `config.py` has a fallback mechanism if this marker isn't found, but creating it ensures consistent path resolution.*

3.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Activate the virtual environment
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

4.  **Install dependencies:**
    Ensure you have the `requirements.txt` file from the repository.
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Application paths and core settings are managed in `prod/code/config.py`. Key configurable items include:
* Database file location (`time_tracker_data.sqlite`).
* Report export directory.
* Icon paths.
* Default and minimum break time intervals.

The script attempts to create necessary directories (e.g., for database, reports) if they don't exist. The database is automatically initialized on first run.

## Running the Application

Once dependencies are installed, run the main script:

```bash
python prod/code/main.py
```

The application will automatically:
- Initialize the SQLite database if it doesn't exist
- Create necessary directories for data storage
- Start tracking window activity in the background
- Display the main UI window

## Data Storage

### Database Structure

The application uses **SQLite** as its primary data storage mechanism:

* **`time_entries` table:** Stores all time tracking data
    * Records: date, program name, window title, category, start/end times, duration
    * Automatically indexed for fast queries by date, program, and category
    
* **`program_categories` table:** Stores program-to-category mappings
    * Replaces the old `user_programs.json` file
    * Allows bulk updates and historical category changes

### Database Location

The database file (`time_tracker_data.sqlite`) is stored in:
```
prod/lib/timeLog/time_tracker_data.sqlite
```

### Data Export

While the primary storage is SQLite, you can export data to CSV:
* **Activity Reports:** Export summarized data (time per category per day) via the UI
* **Date Range Selection:** Export specific time periods
* **Full Export:** Export all historical data

### Migration from CSV (if applicable)

If you have existing CSV data, migration scripts are available in `prod/code/`:
- `migrate_data_to_sqlite.py` - Migrates CSV logs to SQLite
- `apply_migration_sql.py` - Applies SQL migration scripts

## Architecture & Thread Safety

The application uses a **multi-threaded architecture** with proper thread safety:

* **Background Thread:** `WindowTracker` runs in a separate thread to continuously monitor window activity
* **Main Thread:** Handles all GUI operations and user interactions
* **Queue-Based Communication:** Thread-safe queue system ensures GUI operations (like category dialogs) are executed on the main thread
* **Database Connections:** Context manager pattern ensures proper connection handling and prevents leaks

This architecture prevents crashes and ensures smooth operation even when new programs are detected during tracking.

## Usage

### Automatic Tracking

The application automatically starts tracking when launched. It monitors the active window every second and logs time spent in each application.

### Categorization

When a new program is detected:
1. A dialog appears asking you to categorize the program
2. You can select from existing categories or create a new one
3. The category is saved to the database for future use
4. You can edit categories later via "Edit Program Categories" button

### Break Timer

- Set your preferred break interval (default: 50 minutes)
- The timer counts down and alerts you when break time is reached
- Use pause/resume to control the timer
- Reset to restart the countdown

### Viewing Graphs

Click "Show Usage Graph" to see:
- Bar chart comparing today's vs. overall time by category
- Productivity statistics
- Top 10 most used programs

### Exporting Reports

1. Click "Export Activity Report"
2. Choose "All Data" or "Date Range"
3. If using date range, enter start and end dates (DD/MM/YYYY format)
4. Select save location
5. Report is exported as CSV with time per category per day

## Known Issues

None currently. Please report any issues via the repository's issue tracker.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
