# Time Tracker — status

## Completed

- [x] Restructured app under `src/` (PyWebView + WebView2)
- [x] Split `LoggerService`, `GraphService`, decoupled `WindowTracker`
- [x] `CategoryCoordinator` for thread-safe category prompts
- [x] Bridge API (`TimeTrackerApi`) and HTML/JS/CSS frontend
- [x] Deprecated Tkinter entry (`prod/code/main.py` redirect)
- [x] Fix dev crash: ignore self WebView process; category prompts via dashboard poll (not tracker thread UI calls)
- [x] Fix edit-program category modal (no nested `showModal`)
- [x] Web UI audit: a11y (modals, alerts, labels, skip link), XSS escape, local Chart.js, loading overlay
- [x] Web UI round 2: blocking coordinator, modal focus fix, wizard restore, chart a11y table

## Next steps

- [ ] Manual test on Windows: tracking, category prompt, graph, export, exit
- [ ] Run `prod/gen_exe.py` and verify installer on clean VM
- [ ] Update README run instructions to `python src/web_app.py`

## Run (dev)

```powershell
cd time_logger
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe src/web_app.py
```
