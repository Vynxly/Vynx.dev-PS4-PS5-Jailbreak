@echo off
title Vynx.dev Jailbreak
cd /d "%~dp0"

set "PORT=8080"
set "IP="

REM Automatically grab the local 192.168.x.x address
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /i "IPv4" ^| findstr "192.168."') do (
    set "IP=%%A"
)

REM Remove spaces
set "IP=%IP: =%"

echo.
echo ========================================
echo           Vynx.dev Jailbreak
echo ========================================
echo.

if not defined IP (
    echo ERROR: Could not detect your LAN IPv4 address.
    echo.
    ipconfig | findstr /i "IPv4"
    echo.
    pause
    exit /b
)

echo PC IP: %IP%
echo.
echo On your console open:
echo.
echo     http://%IP%:%PORT%
echo.
echo ========================================
echo Press CTRL+C to stop the server.
echo ========================================
echo.

py -3 -m http.server %PORT% --bind 0.0.0.0

pause