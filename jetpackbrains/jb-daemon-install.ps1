New-Service -Name "JB-Daemon" -BinaryPathName "cmd /c C:\Aegentix\jetpackbrains\jb-daemon-launcher.cmd" -DisplayName "JetpackBrains Sovereign Daemon" -StartupType Automatic
Start-Service JB-Daemon
