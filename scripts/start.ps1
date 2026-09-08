# Start Flask app using the venv Python
$venvPython = Join-Path -Path $PSScriptRoot -ChildPath "..\venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    Write-Host "venv Python not found at $venvPython. Create a venv first: python -m venv venv"
    exit 1
}
& $venvPython (Join-Path $PSScriptRoot "..\app.py")
