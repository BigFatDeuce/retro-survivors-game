@echo off
rem Retro Survivors - builds the Linux AppImage from Windows: dist\RetroSurvivors-<version>-x86_64.AppImage
rem Double-click it (or run it from a terminal). Needs Python 3, and Internet the first time (Electron for Linux, the
rem AppImage runtime and squashfs tools, then kept in dist\cache). On the Linux PC: chmod +x the copied file, then run it.
rem Runs tools\make_appimage.py.
setlocal
set "SELF=%~nx0"
cd /d "%~dp0"
call tools\win\find_python.bat || goto :fail
%PY% tools\make_appimage.py %* || goto :fail
echo %cmdcmdline% | find /i "%SELF%" >nul && start "" explorer dist
call :pause_if_clicked
exit /b 0

:fail
echo.
echo FAILED: the build did not finish (see the messages above).
call :pause_if_clicked
exit /b 1

:pause_if_clicked
echo %cmdcmdline% | find /i "%SELF%" >nul && pause
exit /b 0
