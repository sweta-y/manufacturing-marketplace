@echo off
REM Compile cost_estimator.c to cost_estimator.exe
REM This script requires gcc to be installed and available in PATH

cd /d "%~dp0"

echo Checking for gcc...
where gcc >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: gcc compiler not found!
    echo.
    echo To compile the cost estimator, install MinGW-w64:
    echo   1. Download from: https://www.mingw-w64.org/
    echo   2. Or install via Chocolatey: choco install mingw
    echo   3. Or install via winget: winget install mingw
    echo.
    echo After installation, ensure the bin directory is in your PATH.
    echo.
    echo NOTE: The app will use a Python fallback estimator until the C
    echo executable is compiled. Once you compile it, the C version will
    echo automatically be used for more accurate cost estimation.
    echo.
    exit /b 1
)

echo Found gcc, compiling...
gcc -o cost_estimator.exe cost_estimator.c

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: cost_estimator.exe compiled!
    echo.
) else (
    echo.
    echo ERROR: Compilation failed!
    echo.
    exit /b 1
)
