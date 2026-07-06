@echo off
echo [SOVEREIGN] Initializing...
net user sovereign /add 2>nul
mkdir C:\ProgramData\SOVEREIGN\logs 2>nul
netsh advfirewall firewall add rule name=SOVEREIGN-Agent dir=in action=allow protocol=tcp localport=8443
sc create SovereignAgent binPath= C:\SOVEREIGN\Sovereign-System\os-services\agentd.exe start= auto
echo [OK] Done
