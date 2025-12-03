@echo off
echo ========================================
echo Restarting Jarvis AI with Diagnostics
echo ========================================
echo.

REM Clear Python cache
echo Clearing Python cache...
for /d /r "jarvis" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Clear debug log
if exist "c:\Users\lenovo\jarvis_debug.log" del "c:\Users\lenovo\jarvis_debug.log"

echo Stopping any running Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Jarvis with diagnostic logging...
echo Debug log will be written to: c:\Users\lenovo\jarvis_debug.log
echo.

cd /d "%~dp0"
python jarvis/app.py

echo.
echo ========================================
echo Jarvis stopped. Check debug log at:
echo c:\Users\lenovo\jarvis_debug.log
echo ========================================
pause
