# Time Tracker

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md) The Time Tracker is a Python application designed to monitor application usage on your computer, categorize the time spent, and provide insights through logs, graphs, and reports.

## Table of Contents

* [Features](#features)
* [Technical Stack](#technical-stack)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
* [Project Structure](#project-structure)
* [Usage](#usage)
    * [Automatic Tracking](#automatic-tracking)
    * [Categorization](#categorization)
    * [Break Timer](#break-timer)
    * [Viewing Graphs](#viewing-graphs)
    * [Exporting Reports](#exporting-reports)
* [Data Storage](#data-storage)
* [Known Issues](#known-issues)
* [Contributing](#contributing)
* [License](#license)

## Features

* **Automatic Window Detection:** Monitors the currently active window and associated application.
* **Dynamic Category Assignment:**
    * Prompts users to assign categories to newly detected applications.
    * Remembers categories for future use, stored in `user_programs.json`.
    * Provides a UI to edit program-to-category mappings.
* **Detailed Time Logging:** Records start time, end time, and duration for each application window session.
* **Session-Based Percentage Calculation:** Calculates the percentage of time spent in each application per day.
* **CSV Data Output & Archival:**
    * Saves logs to a primary `time_log.csv` file.
    * Archives logs monthly to a `log/` subdirectory.
    * Generates corresponding monthly summary reports to a `report/` subdirectory.
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
* **Theming:** Basic UI theming for a consistent look and feel.

## Technical Stack

* **Language:** Python 3
* **Core Libraries:**
    * `Tkinter` for the GUI.
    * `pandas` for data manipulation and CSV handling.
    * `psutil` for process information.
    * `pywin32` for Windows-specific API interactions (active window detection).
    * `matplotlib` for generating graphs.
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
* Log file locations (main log, historical archives, reports).
* Path to `user_programs.json` for category mappings.
* Icon paths.
* Default and minimum break time intervals.

The script attempts to create necessary directories (e.g., for logs, reports) if they don't exist.

## Running the Application

Once dependencies are installed, run the main script:

```bash
python prod/code/main.py
