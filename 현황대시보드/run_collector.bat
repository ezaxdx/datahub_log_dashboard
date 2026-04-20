@echo off
rem EZ DATAHUB AUTO SYNC
echo Starting data sync and risk detection...
echo Current time: %date% %time%

cd /d "c:\김연아\Antigravity\현황대시보드"

set PYTHON_EXE="C:\Users\EZPMP\AppData\Local\Python\pythoncore-3.14-64\python.exe"

echo [1/2] Syncing Google Sheets data...
%PYTHON_EXE% "* py\collector.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Data sync failed.
    timeout /t 10
    exit /b %ERRORLEVEL%
)

echo [2/2] Checking email notifications...
%PYTHON_EXE% "trigger_notif.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Notification check failed.
    timeout /t 10
    exit /b %ERRORLEVEL%
)

echo ======================================================
echo  All tasks completed successfully.
echo ======================================================
timeout /t 5
