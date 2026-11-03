@echo off
title Drive E Error Check and Repair
echo ========================================================
echo        REPAIRING AND SCANNING DRIVE E: (WD Elements)
echo ========================================================
echo.

:: Check for Administrative Privileges and Elevate
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges (Please click YES on popup)...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo [OK] Running with Administrator Privileges.
echo.
echo [1/2] Checking current status of Drive E:...
fsutil dirty query E:
echo.

echo [2/2] Running Windows NTFS Online Scan on Drive E:...
echo (Yeh scan aapka koi data delete nahi karega, sirf file system ko fix karega)
echo.
chkdsk E: /scan /perf
echo.

echo --------------------------------------------------------
echo Re-checking status after scan:
fsutil dirty query E:
echo --------------------------------------------------------
echo.
echo [DONE] Drive E scan complete!
pause
