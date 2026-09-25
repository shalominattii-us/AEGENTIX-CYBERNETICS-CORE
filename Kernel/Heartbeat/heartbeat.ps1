param()

 = Get-Content -Raw -Path "C:/Aegentix/Kernel/kernel.config.json" | ConvertFrom-Json

while (True) {
     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path "/heartbeat.log" -Value "[HEARTBEAT] "

    Start-Sleep -Milliseconds .heartbeat_interval_ms
}