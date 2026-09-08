Project Solution Guide

Purpose
- Provide a minimal "solution" scaffold to run, test and debug the project locally.

Prerequisites
- Python 3.11+ recommended (project works on 3.14 but some binary wheels may vary)
- Git and VS Code (optional)

Quick setup (Windows PowerShell)

1. Create a virtual environment (if not present):

```powershell
python -m venv venv
```

2. Install dependencies:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Start the app:

```powershell
venv\Scripts\python.exe app.py
```

4. Open the site in your browser:

http://127.0.0.1:5000

Run tests

```powershell
venv\Scripts\python.exe -m pytest -q
```

VS Code debugging

- Open the workspace in VS Code.
- Start the `Launch Flask (venv)` configuration in the Run panel.

Included files

- `.vscode/launch.json` — debug configuration (uses venv Python path)
- `.vscode/tasks.json` — helper tasks to run server and tests from VS Code
- `scripts/start.ps1` — PowerShell script to run the app using the venv Python
- `scripts/start.sh` — POSIX shell script to run the app (macOS/Linux)

Notes
- If you want password reset emails to be sent for real users, configure SMTP in `config.py` and implement email sending in `routes/auth.py`. For local testing the reset token is returned in the API response and pre-filled in the UI.

Contact
- If anything fails during setup, run the commands above and paste terminal output back here and I'll debug further.