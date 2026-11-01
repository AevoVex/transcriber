@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" install_ollama.py %*
) else (
  python install_ollama.py %*
)

if errorlevel 1 pause
endlocal
