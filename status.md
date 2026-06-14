# Time Tracker — status

## Completed

- [x] Restructured app under `src/` (PyWebView + WebView2)
- [x] Split `LoggerService`, `GraphService`, decoupled `WindowTracker`
- [x] `CategoryCoordinator` for thread-safe category prompts
- [x] Bridge API (`TimeTrackerApi`) and HTML/JS/CSS frontend
- [x] Deprecated Tkinter entry (`prod/code/main.py` redirect)
- [x] PyInstaller + Inno Setup build (`prod/gen_exe.py`, `prod/create_installer.iss`)

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
