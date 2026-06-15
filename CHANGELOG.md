# CHANGELOG


## v0.2.1 (2026-06-15)

### Bug Fixes

- **tracker**: Non-blocking category prompts via dashboard poll
  ([`b3491b0`](https://github.com/Amirlabai/time_logger/commit/b3491b0f790834bab1549794366b9a6ef40b2fb7))

Tracker thread blocking on UI caused deadlocks when foreground was the app. Prompts and break
  reminders ride get_dashboard_state(); ignore msedgewebview2/python exe.

Co-authored-by: Cursor <cursoragent@cursor.com>

### Chores

- Update latest.json for 0.2.0
  ([`4999ab9`](https://github.com/Amirlabai/time_logger/commit/4999ab9b647f05f4d4d1cf173fff74ca0e555a75))


## v0.2.0 (2026-06-14)

### Features

- **ui**: Lift window and add update checks
  ([`4dc7b92`](https://github.com/Amirlabai/time_logger/commit/4dc7b92e4090599cf9f4dce986f28934b73171a7))

Category prompt must surface above the active app during tracking.

Fetch latest.json from main; CI commits manifest after installer build.

Co-authored-by: Cursor <cursoragent@cursor.com>


## v0.1.0 (2026-06-14)

### Continuous Integration

- **release**: Add semantic-release and installer workflow
  ([`730752b`](https://github.com/Amirlabai/time_logger/commit/730752b75860f0d8d09233a8ee4f7aca190bc92e))

Tag vX.Y.Z on conventional commits to main; Windows job builds Inno installer and uploads to that
  release.

Co-authored-by: Cursor <cursoragent@cursor.com>

### Features

- Implement interactive report viewing and enhanced export
  ([`91e1298`](https://github.com/Amirlabai/time_logger/commit/91e12982a3a6deeddacca3f8dff94b3ce32e9ae4))

This commit introduces a new interactive report viewing feature and modifies the export
  functionality.

Key changes:

1. **Interactive Report Window**: - The "Export Activity Report" button now opens a new "Activity
  Report" window instead of directly triggering a file export. - This window displays activity data
  in a tabular format using a `ttk.Treeview`.

2. **Dynamic Date Filtering**: - You can filter the report data by selecting a start and end date
  within the new report window. - A "Refresh Data" button updates the displayed report based on the
  selected date range.

3. **View Switching**: - You can switch between a "Detailed Log View" and a "Summary Report View"
  using radio buttons. - The "Detailed Log View" shows raw activity logs (timestamp, application,
  window title, category, duration). - The "Summary Report View" shows aggregated data (date,
  category, program name, total time). - The Treeview columns and content dynamically update based
  on the selected view.

4. **Contextual Export**: - The "Export to CSV" button in the report window now exports the data
  currently displayed in the Treeview. - This means if you have filtered by date or switched to the
  summary view, the exported CSV will reflect that exact view. - The underlying
  `Logger.export_activity_report` method was modified to accept a DataFrame, allowing the UI to
  control what data is exported.

5. **UI Enhancements**: - The new report window includes date entry fields, refresh and export
  buttons, and view selection radio buttons. - Basic theming is applied for consistency. - The main
  `TimeTrackerUI.open_export_report_dialog` was refactored to call the new `show_report_window`
  method. Helper methods `_populate_report_treeview` and `_prepare_and_display_report_data` were
  added to manage report display and view logic.

- **ui**: Migrate Tkinter to PyWebView
  ([`e7382b6`](https://github.com/Amirlabai/time_logger/commit/e7382b64857097ddc39682b9e8e2ccbfa00b20c6))

WebView2 replaces Tk widgets; Python bridge keeps tracking and SQLite.

Add PyInstaller + Inno pipeline for Windows installer output.

Entry point is src/web_app.py; prod/code/main.py redirects.

Co-authored-by: Cursor <cursoragent@cursor.com>
