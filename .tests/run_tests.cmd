@echo off
REM Run PowerShell test suite
REM This batch file launches the PowerShell test runner

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "run_tests.ps1"
pause
