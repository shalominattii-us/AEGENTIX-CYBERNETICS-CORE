function JB-Log { param([string]$msg) $ts=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss"); Add-Content -Path "C:\Aegentix\jetpackbrains\jb-daemon.log" -Value "$ts $msg" }
