# Control Plane - State Management
param([string]$Control, [string]$State)

function Get-SystemState {
    $state = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        host = $env:COMPUTERNAME
        services = @{
            node = (Get-Process node -ErrorAction SilentlyContinue) -ne $null
            powershell = (Get-Process powershell -ErrorAction SilentlyContinue).Count
            daemon = (Test-Path "C:\Aegentix\jetpackbrains\jb-daemon.ps1")
        }
        resources = @{
            memory = (Get-Counter "\Memory\Available MBytes").CounterSamples.CookedValue
            disk = (Get-PSDrive C).Free / 1GB
        }
        agents = Get-ChildItem C:\Aegentix\agents\ -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }
    }
    return $state
}

function Set-SystemState {
    param([string]$Key, [string]$Value)
    $stateFile = "C:\Aegentix\control\state\system-state.json"
    $state = if (Test-Path $stateFile) { Get-Content $stateFile | ConvertFrom-Json } else { @{} }
    $state.$Key = $Value
    $state.timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    $state | ConvertTo-Json | Set-Content $stateFile
}

function Invoke-Control {
    param([string]$Control, [string]$State)
    switch ($Control) {
        "state" { Get-SystemState }
        "set" { Set-SystemState -Key $State -Value "set" }
        "health" { Get-SystemState }
        default { Write-Host "[CONTROL] Unknown control: $Control" -ForegroundColor Red }
    }
}

Export-ModuleMember -Function Invoke-Control
