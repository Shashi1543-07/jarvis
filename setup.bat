@echo off
echo Jarvis AI Setup
echo =================

echo Changing directory to 'jarvis'...
cd jarvis
if %errorlevel% neq 0 (
    echo Error: Could not find 'jarvis' directory.
    pause
    exit /b 1
)

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Python is not found! Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo ERROR: Failed to install requirements.
    echo Please check the error message above.
    echo Common fixes:
    echo  - Install Visual C++ Build Tools (for pyaudio/pyttsx3)
    echo  - Ensure internet connection is active
    echo ========================================================
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
pause
