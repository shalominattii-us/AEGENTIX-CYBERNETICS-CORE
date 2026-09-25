@echo off
echo Starting AEGENTIX System...
cd C:\Aegentix
docker compose up -d
echo All services started!
echo HUD: http://localhost:3000
echo Runtime: http://localhost:8080
echo GAIA: http://localhost:8090
pause
