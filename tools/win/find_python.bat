@echo off
rem Sets PY to a working Python 3 for the .bat scripts at the repository's root: "python", else the "py -3" launcher.
rem ("where python" is not enough: Windows ships a python.exe alias that only opens the Microsoft Store.)
rem Usage, from a root script after setlocal:   call tools\win\find_python.bat || goto :fail
set "PY="
python -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && set "PY=python"
if not defined PY (py -3 -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && set "PY=py -3")
if not defined PY (
  echo Python 3.8 or newer was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add Python to PATH" during the installation, then run this script again.
  exit /b 1
)
exit /b 0
