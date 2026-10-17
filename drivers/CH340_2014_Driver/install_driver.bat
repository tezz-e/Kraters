@echo off
setlocal
title CH340 2014 Driver Installer

echo ========================================================
echo     CH340 / CH341 2014 WORKING LEGACY DRIVER INSTALLER
echo ========================================================
echo.

:: Check for administrative rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [..] Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo [..] Installing CH340 2014 driver (Version 3.4.2014.08)...
pnputil /add-driver "%~dp0ch341ser.inf" /install

if %errorLevel% equ 0 (
    echo.
    echo ========================================================
    echo  [SUCCESS] Driver installed into Windows successfully!
    echo ========================================================
    echo  Please unplug and re-plug your ESP8266 USB cable now.
    echo.
) else (
    echo.
    echo [INFO] Alternatively, you can right-click 'ch341ser.inf'
    echo        in this folder and select 'Install'.
    echo.
)

pause
