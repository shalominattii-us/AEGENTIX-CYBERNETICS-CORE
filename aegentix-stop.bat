@echo off
echo Stopping AEGENTIX System...
cd C:\Aegentix
docker compose down
echo All services stopped!
pause
