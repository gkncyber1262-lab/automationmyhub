@echo off
title Cyber Intelligence All-In-One Servers Launcher
echo =================================================================
echo        CYBER CRIME INVESTIGATION - MASTER MULTI-SERVER LAUNCHER
echo =================================================================
echo.

echo [1/4] Checking MongoDB Windows Service (Port 27017)...
sc query MongoDB | find "RUNNING" >nul
if %ERRORLEVEL% equ 0 (
    echo   -^> MongoDB Case DB (Port 27017) is RUNNING.
) else (
    echo   -^> Starting MongoDB Windows Service...
    net start MongoDB
)
echo.

echo [2/4] Checking MongoDB 15.66M Cell Master Instance (Port 27018)...
netstat -ano | find "27018" | find "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo   -^> MongoDB 15.66M Cell Master (Port 27018) is already RUNNING.
) else (
    echo   -^> Starting MongoDB Port 27018 with 15.66M Cell Database...
    start /b "" "C:\Program Files\MongoDB\Server\9.0\bin\mongod.exe" --dbpath "D:\CELL ID 22-10-2026\MONGODB_DATA\db" --port 27018 --logpath "D:\CELL ID 22-10-2026\MONGODB_DATA\log\mongod.log" --logappend
    echo   -^> Started MongoDB Port 27018 in background.
)
echo.

echo [3/4] Checking Master 560GB Database on E:\Database (Port 27019)...
netstat -ano | find "27019" | find "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo   -^> Master E:\Database (Port 27019) is already RUNNING.
) else (
    if exist "E:\Database" (
        echo   -^> Starting Master 560GB Database on Port 27019...
        if exist "E:\Database\mongod.lock" echo. > "E:\Database\mongod.lock"
        start /b "" "C:\Program Files\MongoDB\Server\9.0\bin\mongod.exe" --dbpath "E:\Database" --port 27019 --logpath "D:\mongod_e_db.log" --logappend --wiredTigerCacheSizeGB 4
    ) else (
        echo   -^> [NOTE] E:\Database drive is not attached or offline.
    )
)
echo.

echo [4/4] Checking REST API Server (Port 8000)...
netstat -ano | find "8000" | find "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo   -^> REST API Server (Port 8000) is already RUNNING.
) else (
    echo   -^> Starting REST API Server on http://127.0.0.1:8000 ...
    start "" python api_server.py
    echo   -^> REST API Server started.
)
echo.

echo =================================================================
echo [OK] ALL SERVICES & APIS ARE CONFIGURED!
echo   * Web Dashboard:  http://localhost:8000/
echo   * Swagger Docs:   http://localhost:8000/docs
echo   * Master API Key: CYBER-INTEL-MASTER-2026-X9K4R2
echo   * Officer Key:    CYBER-OFFICER-INVESTIGATION-KEY-8821
echo =================================================================
pause
