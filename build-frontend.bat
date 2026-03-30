@echo off
echo ========================================
echo NemhemAI - Frontend Build Script
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo [2/3] Building React frontend...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
echo.

echo [3/3] Verifying build...
if exist dist\index.html (
    echo.
    echo ========================================
    echo FRONTEND BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Output: dist\
    echo.
    echo Next step: Run build-lowmem.bat to create EXE
    echo.
) else (
    echo ERROR: Build completed but dist\index.html not found!
    pause
    exit /b 1
)

pause
