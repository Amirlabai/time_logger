# Time Tracker

This Python script tracks the time you spend in different applications on your computer and categorizes that time. It logs the active window (application), 
the category you assign to it, start and end times, and calculates the percentage of time spent in each application within a session (a day).  The data is saved to a CSV file.

## Features

*   **Automatic Window Detection:** Monitors the currently active window (application).
*   **Category Assignment:** Prompts you to assign categories to applications.  It remembers these categories for future use.
*   **Time Logging:** Records the start and end times for each window activation.
*   **Session-Based Percentage Calculation:** Calculates the percentage of time spent in each application *per day* (session).  Percentages are calculated *after* the logging session is complete for accurate daily totals.
*   **CSV Output:** Saves the logged data to a CSV file (specified by the user).
*   **File Selection:** Allows the user to choose the CSV file to use via a file dialog.
*   **Error Handling:** Attempts to handle cases where the CSV file is already open.

## Requirements

*   Python 3
*   Libraries: `pandas`, `psutil`, `pywin32`, `tkinter`

You can install the necessary libraries using pip:

```bash
pip install pandas psutil pywin32
