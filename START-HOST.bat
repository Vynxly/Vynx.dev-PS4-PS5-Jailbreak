@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "HOST_SCRIPT="
for /f "delims=" %%F in ('dir /b /o-n "vynx-autoloader-host_v*.py" 2^>nul') do if not defined HOST_SCRIPT set "HOST_SCRIPT=%%F"
if not defined HOST_SCRIPT if exist "vynx-autoloader-host.py" set "HOST_SCRIPT=vynx-autoloader-host.py"

if not defined HOST_SCRIPT (
  echo No built Vynx autoloader host was found.
  echo Run build_release.sh first, then copy this launcher beside the generated host script.
  pause
  exit /b 1
)

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher "py" was not found. Install Python 3 from python.org.
  pause
  exit /b 1
)

py -3 "%HOST_SCRIPT%"
if errorlevel 1 pause
