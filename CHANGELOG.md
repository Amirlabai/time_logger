# CHANGELOG


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
