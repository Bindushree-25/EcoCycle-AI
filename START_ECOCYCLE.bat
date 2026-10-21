@echo off
setlocal EnableExtensions
chcp 65001 >nul
title EcoCycle AI - Flagship Studio Release
set "TARGET=C:\EcoCycleAI"
set "SOURCE=%~dp0."

echo.
echo  EcoCycle AI - Flagship Studio Release
echo  -------------------------------------
echo  Short-path setup prevents Windows TensorFlow long-path errors.
echo  Internet is required for dependency and first model downloads.
echo.

rem If launched from the target folder, do not copy the project onto itself.
for %%I in ("%~dp0.") do set "SOURCE_FULL=%%~fI"
for %%I in ("%TARGET%") do set "TARGET_FULL=%%~fI"
if /I "%SOURCE_FULL%"=="%TARGET_FULL%" goto target_ready

echo [1/4] Copying project to %TARGET% ...
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 goto failed
rem The \.: suffix prevents a trailing-backslash quote parsing issue in cmd.exe.
robocopy "%SOURCE%" "%TARGET%" /E /R:2 /W:1 /XD .venv __pycache__ hf_model_cache .git /XF *.pyc /NFL /NDL /NJH /NJS /NP
if errorlevel 8 goto copy_failed

echo Project copy complete.
:target_ready
cd /d "%TARGET%"
if errorlevel 1 goto failed

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher 'py' was not found.
  echo Install Python 3.11 from https://www.python.org/downloads/release/python-3119/
  echo During installation, enable the Python launcher option.
  pause
  exit /b 1
)

py -3.11 -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.11 is not installed.
  echo Install Python 3.11 from https://www.python.org/downloads/release/python-3119/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [2/4] Creating isolated Python 3.11 environment...
  py -3.11 -m venv .venv
  if errorlevel 1 goto failed
) else (
  echo [2/4] Reusing Python environment at %TARGET%\.venv
)

echo [3/4] Installing application and AI dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [4/4] Starting EcoCycle AI...
echo Open http://127.0.0.1:5000 in your browser.
echo Keep this window open while using the app.
start "EcoCycle AI Browser" http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto failed
exit /b 0

:copy_failed
echo ERROR: Could not copy project to %TARGET%.
echo Close any running EcoCycle AI instance and check folder permissions.
pause
exit /b 1

:failed
echo.
echo Setup/startup failed. Read the error above.
pause
exit /b 1
