@echo off
rem Retro Survivors - builds the Android APK: dist\RetroSurvivors-<version>.apk
rem Double-click it (or run it from a terminal). Needs Python 3, and Internet the first time: Google's Android build tools
rem (after you accept their licence) and a JDK if javac is missing, kept in dist\cache\android.
rem The signing key is %USERPROFILE%\.retro-survivors\android.keystore: keep it, updates must be signed with the same key.
rem On the phone: copy the .apk file and open it (allow installing unknown apps). Runs tools\make_apk.py.
setlocal
set "SELF=%~nx0"
cd /d "%~dp0"
call tools\win\find_python.bat || goto :fail
%PY% tools\make_apk.py %* || goto :fail
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
