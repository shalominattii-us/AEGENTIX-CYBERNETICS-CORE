Write-Host "[ESS7] Initializing environment..."

$logPath = "$PSScriptRoot\06_Logs"
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath | Out-Null
}

Write-Host "[ESS7] Environment ready."
