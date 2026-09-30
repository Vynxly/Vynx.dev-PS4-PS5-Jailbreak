@echo off
setlocal EnableExtensions
title Vynx.dev Jailbreak
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    cls
    echo.
    echo ============================================
    echo          Vynx.dev Jailbreak - ERROR
    echo ============================================
    echo.
    echo Python 3 is required.
    echo Download it from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

cls
echo.
echo ============================================
echo             Vynx.dev Jailbreak
echo ============================================
echo.
echo             Starting...
echo.
echo     Setting up the local jailbreak host.
echo             Please wait.
echo.

%PYTHON_CMD% "%~dp0local_host.py"
set "HOST_EXIT=%ERRORLEVEL%"

if not "%HOST_EXIT%"=="0" (
    echo.
    echo The host could not start.
    echo Try right-clicking .START-HOST.bat and choosing
    echo "Run as administrator", then try again.
    echo.
    pause
)

exit /b %HOST_EXIT%
