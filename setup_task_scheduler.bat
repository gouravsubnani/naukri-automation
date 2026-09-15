@echo off
REM ============================================================
REM Creates a Windows Task Scheduler entry that runs the Naukri
REM automation every day at 09:00 AM.
REM 
REM Run this script AS ADMINISTRATOR (right-click > Run as admin)
REM ============================================================

SET TASK_NAME=NaukriResumeAutomation
SET PYTHON_PATH=python
SET SCRIPT_PATH=%~dp0scheduler.py
SET WORK_DIR=%~dp0

echo.
echo Creating scheduled task: %TASK_NAME%
echo Script: %SCRIPT_PATH%
echo Schedule: Daily at 09:00 AM
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --now" ^
    /sc daily ^
    /st 09:00 ^
    /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task created successfully!
    echo The automation will run every day at 9:00 AM.
    echo.
    echo To verify:  schtasks /query /tn "%TASK_NAME%"
    echo To delete:  schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo Failed to create task. Make sure you run this as Administrator.
)

echo.
pause
