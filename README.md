# Time Tracker

This Python script tracks the time you spend in different applications on your computer and categorizes that time. It logs the active window (application), 
the category you assign to it, start and end times, and calculates the percentage of time spent in each application within a session (a day).  The data is saved to a CSV file.

Note: For best results have a designated window for breaks, even if your computer sleeps when inactive. For laptops closing the screen can be categorized as break also along with sleep.

## Features

*   **Automatic Window Detection:** Monitors the currently active window (application).
*   **Category Assignment:** Prompts you to assign categories to applications.  It remembers these categories for future use(for some odd reason it does remember but cant submit selection from the drop down menu).
*   **Time Logging:** Records the start and end times for each window activation.
*   **Session-Based Percentage Calculation:** Calculates the percentage of time spent in each application *per day* (session).  Percentages are calculated *after* the logging session is complete for accurate daily totals.
*   **CSV Output:** Saves the logged data to a CSV file (specified by the user). To rest either move or delete the CSV file, program creates it.
*   **Error Handling:** Attempts to handle cases where the CSV file is already open. Must be closed to open through script
*   **Graph Plot:** Shows session percentage along with total time spent. Graph window has on top total span of days and it calculates productivity
*   **Break Timer:** Running timer with minimum of 10 minutes and a pop up alert to take a break

## Requirements

*   Python 3
*   Libraries: `pandas`, `psutil`, `pywin32`, `tkinter`, `time`, `win32process`, `os`, `matplotlib`, `traceback`, `threading`

You can install the necessary libraries using pip:
win32gui is pywin32
```bash
pip install pandas etc...
```
