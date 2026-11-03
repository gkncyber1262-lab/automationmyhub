@echo off
title NCRP Unified Master Agent - Cyber Police Station North District
chcp 65001 >nul
cls

if "%~1"=="" (
    python ncrp_master_agent.py --interview
    goto FINISH
)

set "FIRST_ARG=%~1"
if "%FIRST_ARG:~0,2%"=="--" (
    python ncrp_master_agent.py %*
    goto FINISH
)

echo [INFO] Processing NCRP Case File: %~1
python ncrp_master_agent.py --case "%~1"

:FINISH
echo.
echo ======================================================================================
echo Case processing finished. Press any key to exit...
echo ======================================================================================
pause >nul
