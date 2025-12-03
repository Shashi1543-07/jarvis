@echo off
echo ============================================
echo    Jarvis AI - API Key Setup
echo ============================================
echo.
echo To enable Jarvis's intelligence, you need a Google Gemini API key.
echo.
echo Step 1: Get your FREE API key
echo    Visit: https://aistudio.google.com/app/apikey
echo    Click "Create API Key"
echo    Copy the key
echo.
echo Step 2: Enter your API key below
echo.
set /p API_KEY="Paste your API key here: "

echo.
echo Saving API key...

cd jarvis\config
(
echo {
echo     "GEMINI_API_KEY": "%API_KEY%"
echo }
) > secrets.json

echo.
echo ============================================
echo    API Key saved successfully!
echo ============================================
echo.
echo You can now run Jarvis with full intelligence:
echo    .\run.bat
echo.
pause
