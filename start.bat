@echo off
title NemhemAI Launcher
echo.
echo ====================================
echo Starting NemhemAI...
echo ====================================
echo.

REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✓ Ollama is running
) else (
    echo WARNING: Ollama is not running!
    echo Starting Ollama...
    start /B ollama serve
    timeout /t 3 >nul
)

echo.
echo Starting NemhemAI application...
echo Browser will open automatically.
echo.
echo To stop the application, close this window.
echo.

REM Run the EXE
NemhemAI.exe

pause
