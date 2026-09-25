# --- Cognitive Gateway Status Check ---
try {
    \ = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Aegentix\brain\cognitive_gateway.ps1" -Operation status 2>&1
    \ = \ -join "
" | ConvertFrom-Json
    if (\.ok -ne \True) {
        throw "Gateway reported failure."
    }
} catch {
    Write-Host "Cognitive gateway unavailable: \" -ForegroundColor Red
    return
}
param()

Write-Host "[Aegentix] Autonomous Agent Loop Starting..."

 = Get-Content -Raw -Path "agent.config.json" | ConvertFrom-Json

while (True) {

    # Load state
     = Join-Path .state_path "agent.state.json"
    if (Test-Path ) {
         = Get-Content -Raw -Path  | ConvertFrom-Json
    } else {
         = @{ last_action = "none"; cycle = 0 }
    }

    # Increment cycle
    .cycle++

    # Log cycle
     = "[Cycle ] Executing autonomous operations..."
    Add-Content -Path "/loop.log" -Value 

    # Execute MCP servers
    foreach ( in .mcp_servers) {
        Write-Host "[MCP] Executing server at "
        try {
            node "/index.js" | Out-Null
        } catch {
            Add-Content -Path "/errors.log" -Value "[ERROR] MCP server failure: "
        }
    }

    # Execute Cybercore subsystems
    Write-Host "[Cybercore] Running RCE subsystem..."
    try {
        node "/RCE/index.js" | Out-Null
    } catch {
        Add-Content -Path "/errors.log" -Value "[ERROR] RCE failure: "
    }

    Write-Host "[Cybercore] Running Directive Interpreter..."
    try {
        node "/DI/index.js" | Out-Null
    } catch {
        Add-Content -Path "/errors.log" -Value "[ERROR] DI failure: "
    }

    # Save state
     | ConvertTo-Json | Set-Content -Path 

    # Sleep
    Start-Sleep -Milliseconds .loop_interval_ms
}
