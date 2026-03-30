@echo off
echo ====================================
echo NemhemAI - Quick EXE Build
echo (Assumes frontend is already built)
echo ====================================
echo.

REM Check if dist folder exists (frontend build)
if not exist dist (
    echo ERROR: Frontend build not found!
    echo Please run "npm run build" first, or use build.bat for full build.
    pause
    exit /b 1
)

echo [1/3] Installing PyInstaller...
pip install pyinstaller
echo.

echo [2/3] Cleaning previous build...
if exist dist\NemhemAI.exe del /q dist\NemhemAI.exe
if exist build rmdir /s /q build
echo.

echo [3/3] Building EXE...
pyinstaller main.exe.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ====================================
echo Build completed successfully!
echo ====================================
echo.
echo Executable: dist\NemhemAI.exe
echo.
pause
