@echo off
rem Retro Survivors - play the game in your browser straight from this folder (the files as they are now, nothing built).
rem Double-click it. Needs Python 3. Keep the window open while playing; close it (or Ctrl+C) to stop the local server.
rem Options: play_local.bat [port] [--no-browser]   (default: the first free port from 8765) - runs tools\serve_local.py
setlocal
cd /d "%~dp0"
call tools\win\find_python.bat || (pause & exit /b 1)
%PY% tools\serve_local.py %*
if errorlevel 1 (pause & exit /b 1)
exit /b 0
