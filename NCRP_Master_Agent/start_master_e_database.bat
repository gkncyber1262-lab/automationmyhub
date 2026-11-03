@echo off
title Master E-Drive MongoDB (560 GB) Starter
echo =================================================================
echo       STARTING MASTER MONGODB DATABASE (E:\Database - 560 GB)
echo =================================================================
echo.

echo [1/2] Clearing any stale lock file...
if exist "E:\Database\mongod.lock" (
    echo. > "E:\Database\mongod.lock"
)
if exist "E:\Database\journal\WiredTigerTmplog.0000000001" (
    del /f /q "E:\Database\journal\WiredTigerTmplog.0000000001" 2>nul
)

echo [2/2] Starting MongoDB Instance on Port 27019...
"C:\Program Files\MongoDB\Server\9.0\bin\mongod.exe" --dbpath "E:\Database" --port 27019 --logpath "D:\mongod_e_db.log" --logappend --wiredTigerCacheSizeGB 4

echo.
pause
