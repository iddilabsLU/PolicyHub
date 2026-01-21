@echo off
REM PolicyHub Build Script
REM Builds PolicyHub into a Windows executable using PyInstaller
REM
REM Prerequisites:
REM   - Python 3.11+ installed and in PATH
REM   - pip install -r requirements.txt
REM
REM Usage:
REM   build.bat          - Build executable
REM   build.bat clean    - Clean build artifacts
REM   build.bat test     - Run tests before building

setlocal enabledelayedexpansion

echo ============================================
echo PolicyHub Build Script
echo ============================================
echo.

REM Check for clean command
if "%1"=="clean" (
    echo Cleaning build artifacts...
    if exist "build" rmdir /s /q "build"
    if exist "dist" rmdir /s /q "dist"
    if exist "__pycache__" rmdir /s /q "__pycache__"
    echo Clean complete.
    exit /b 0
)

REM Check for test command
if "%1"=="test" (
    echo Running tests...
    python -m pytest -v
    if errorlevel 1 (
        echo Tests failed! Build aborted.
        exit /b 1
    )
    echo Tests passed.
    echo.
)

REM Check Python version
echo Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ and add to PATH.
    exit /b 1
)

REM Check PyInstaller
echo Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build executable
echo.
echo Building PolicyHub executable...
echo This may take a few minutes...
echo.

pyinstaller PolicyHub.spec --noconfirm --distpath build

if errorlevel 1 (
    echo.
    echo ============================================
    echo BUILD FAILED
    echo ============================================
    echo Check the error messages above for details.
    exit /b 1
)

REM Check if build succeeded
if not exist "build\PolicyHub.exe" (
    echo.
    echo ERROR: Build completed but executable not found.
    exit /b 1
)

REM Get file size
for %%A in ("build\PolicyHub.exe") do set size=%%~zA
set /a size_mb=%size% / 1048576

echo.
echo ============================================
echo BUILD SUCCESSFUL
echo ============================================
echo.
echo Executable: build\PolicyHub.exe
echo Size: ~%size_mb% MB
echo.
echo To distribute:
echo   1. Copy build\PolicyHub.exe to target machine
echo   2. Run PolicyHub.exe
echo   3. The app will create its data folder in %%LOCALAPPDATA%%\PolicyHub
echo.

exit /b 0
