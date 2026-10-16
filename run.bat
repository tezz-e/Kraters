@echo off
setlocal enabledelayedexpansion
title Kater's Pendulum Experiment System

echo ========================================================
echo     KATER'S PENDULUM AUTOMATED MEASUREMENT SYSTEM
echo ========================================================
echo.

:: 1. Detect Python
set PYTHON_CMD=
where py >nul 2>&1 && set PYTHON_CMD=py
if "%PYTHON_CMD%"=="" where python >nul 2>&1 && set PYTHON_CMD=python

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python was not found on this computer!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Using Python command: %PYTHON_CMD%

:: 2. Check and auto-install dependencies if missing
echo [..] Checking required libraries (PyQt5, pyqtgraph, pyserial, numpy)...
%PYTHON_CMD% -c "import PyQt5, pyqtgraph, serial, numpy" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [..] Installing required libraries automatically...
    %PYTHON_CMD% -m pip install -r "%~dp0python\requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependency installation failed. Please check internet connection.
        pause
        exit /b 1
    )
)

echo [OK] All dependencies are ready!
echo [..] Launching Kater's Pendulum Application...
echo.

:: 3. Launch application
cd /d "%~dp0python"
%PYTHON_CMD% main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTICE] Application closed with code %ERRORLEVEL%.
    pause
)
