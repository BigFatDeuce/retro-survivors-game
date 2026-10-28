@echo off
rem Retro Survivors - builds the playable Windows game: dist\RetroSurvivors\RetroSurvivors.exe (nothing to install, no zip).
rem Double-click it (or run it from a terminal). Needs Python 3, and Internet the first time (Electron, ~110 MB, then kept
rem in dist\cache). Close the game first: a running RetroSurvivors.exe locks its folder. Runs tools\make_exe.py.
setlocal
set "SELF=%~nx0"
cd /d "%~dp0"
call tools\win\find_python.bat || goto :fail
%PY% tools\make_exe.py %* || goto :fail
echo %cmdcmdline% | find /i "%SELF%" >nul && start "" explorer "dist\RetroSurvivors"
call :pause_if_clicked
exit /b 0

:fail
echo.
echo FAILED: the build did not finish (see the messages above).
call :pause_if_clicked
exit /b 1

:pause_if_clicked
rem (a double-click opens a window that would close at once; a terminal keeps the output)
echo %cmdcmdline% | find /i "%SELF%" >nul && pause
exit /b 0
