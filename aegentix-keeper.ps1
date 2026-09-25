# ============================================================================
#  AEGENTIX KEEPER — self-healing supervisor for the local AI stack
#  Runs at logon + every 15 min via Scheduled Task "AegentixKeeper".
#  Ensures: Docker Desktop, Lemonade Server (:9000 / Ollama-compat :11434),
#           CyberCore LLM container (:7100), Cyberdeck daemon (jb-daemon.ps1).
#  Writes: C:\Aegentix\status\keeper-last.json  +  C:\Aegentix\logs\keeper.log
#  Usage:  powershell -ExecutionPolicy Bypass -File C:\Aegentix\aegentix-keeper.ps1 [-Register] [-Once]
# ============================================================================
param([switch]$Register, [switch]$Once)

$ErrorActionPreference = 'Continue'
$Root      = 'C:\Aegentix'
$LogDir    = "$Root\logs";   $StatusDir = "$Root\status"
$LogFile   = "$LogDir\keeper.log"
$StatusFile= "$StatusDir\keeper-last.json"
$Docker    = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$DockerUI  = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
$Lemonade  = "$env:LOCALAPPDATA\lemonade_server\bin\LemonadeServer.exe"
$Compose   = "$Root\docker-compose.yml"
$JbDaemon  = "$Root\jetpackbrains\jb-daemon.ps1"
New-Item -ItemType Directory -Force -Path $LogDir,$StatusDir | Out-Null

function Log($m){ $l="$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Add-Content -Path $LogFile -Value $l; Write-Host $l }
function Http($url,$timeout=8){ try { (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeout).Content } catch { $null } }
function Wait-Until([scriptblock]$test,[int]$sec){ $t=[Diagnostics.Stopwatch]::StartNew(); while($t.Elapsed.TotalSeconds -lt $sec){ if(& $test){return $true}; Start-Sleep 3 }; return (& $test) }

# ---------------------------------------------------------------- Register
if ($Register) {
    $action  = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Root\aegentix-keeper.ps1`""
    $trig1   = New-ScheduledTaskTrigger -AtLogOn
    $trig2   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
    $settings= New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    Register-ScheduledTask -TaskName 'AegentixKeeper' -Action $action -Trigger $trig1,$trig2 -Settings $settings -RunLevel Highest -Force | Out-Null
    Log "REGISTERED scheduled task AegentixKeeper (logon + every 15 min)"
    if (-not $Once) { return }
}

Log "===== KEEPER RUN START ====="
$S = [ordered]@{ ts=(Get-Date).ToString('o'); host=$env:COMPUTERNAME; components=[ordered]@{}; actions=@(); ok=$true }
function Mark($name,$state,$detail){ $S.components[$name]=[ordered]@{state=$state;detail=$detail}; if($state -ne 'up'){$S.ok=$false}; Log "[$name] $state - $detail" }
function Act($a){ $S.actions += $a; Log "ACTION: $a" }

# ---------------------------------------------------------------- 1. Docker
$dockerUp = { (& $Docker info 2>$null | Select-String 'Server Version') -ne $null }
if (-not (& $dockerUp)) {
    if (-not (Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue)) { Start-Process $DockerUI; Act "started Docker Desktop" }
    if (Wait-Until $dockerUp 150) { Act "Docker engine came up" }
}
if (& $dockerUp) { Mark docker up "engine responding" } else { Mark docker down "engine not responding after 150s" }

# ---------------------------------------------------------------- 2. Lemonade (serves native + Ollama-compat API on :11434)
$lemUp = { (Http 'http://localhost:11434/api/v1/health' 5) -ne $null }
if (-not (& $lemUp)) {
    if (Test-Path $Lemonade) {
        if (-not (Get-Process LemonadeServer -ErrorAction SilentlyContinue)) { Start-Process $Lemonade -ArgumentList '--silent'; Act "started LemonadeServer" }
        if (Wait-Until $lemUp 60) { Act "Lemonade came up" }
    } else { Log "Lemonade not installed at $Lemonade" }
}
if (& $lemUp) {
    $models = (Http 'http://localhost:11434/api/v1/models' 8)
    $names  = @(); try { $names = ((ConvertFrom-Json $models).data | ForEach-Object { $_.id }) } catch {}
    Mark lemonade up ("models: " + ($names -join ', '))
    $S.components.lemonade.models = $names
} else { Mark lemonade down "no response on :11434" }

# ---------------------------------------------------------------- 3. CyberCore LLM container (:7100)
$ccUp = { (Http 'http://localhost:7100/health' 5) -ne $null }
if ((& $dockerUp) -and -not (& $ccUp)) {
    Push-Location $Root
    & $Docker compose -f $Compose up -d aegentix-cybercore-llm 2>&1 | Out-Null
    Pop-Location
    Act "docker compose up aegentix-cybercore-llm"
    Wait-Until $ccUp 60 | Out-Null
}
if (& $ccUp) {
    $h = Http 'http://localhost:7100/health' 5
    Mark cybercore up ($h -replace '\s+',' ' | ForEach-Object { $_.Substring(0,[Math]::Min(160,$_.Length)) })
    # real inference smoke test (tiny model, 8 tokens)
    try {
        $body = @{model='cybercore-tiny';messages=@(@{role='user';content='Say OK'});max_tokens=8} | ConvertTo-Json -Compress
        $r = Invoke-RestMethod -Uri 'http://localhost:7100/v1/chat/completions' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 90
        $txt = $r.choices[0].message.content
        $S.components.cybercore.inference = "ok: $txt"; Log "[cybercore] inference OK -> $txt"
    } catch { $S.components.cybercore.inference = "FAILED: $($_.Exception.Message)"; $S.ok=$false; Log "[cybercore] inference FAILED: $($_.Exception.Message)" }
} else { Mark cybercore down "no /health on :7100" }

# ---------------------------------------------------------------- 4. Cyberdeck daemon (jb-daemon.ps1) as detached process, not a session Job
$jb = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*jb-daemon.ps1*' }
if (-not $jb) {
    if (Test-Path $JbDaemon) {
        Start-Process powershell.exe -ArgumentList "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$JbDaemon`"" -WindowStyle Hidden
        Act "started Cyberdeck daemon (jb-daemon.ps1)"; Start-Sleep 2
        $jb = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*jb-daemon.ps1*' }
    }
}
if ($jb) { Mark cyberdeck up "jb-daemon PID $($jb.ProcessId)" } else { Mark cyberdeck down "jb-daemon not running" }

# ---------------------------------------------------------------- 5. Antigravity (report only)
$ag = Get-Process language_server -ErrorAction SilentlyContinue
if ($ag) { Mark antigravity up "language_server PID $($ag.Id)" } else { Mark antigravity idle "Antigravity app not open (fine)" ; $S.ok = $S.ok }  # idle is not a failure
if ($S.components.antigravity.state -eq 'idle') { $S.ok = ($S.components.Values | Where-Object { $_.state -eq 'down' }).Count -eq 0 }

# ---------------------------------------------------------------- write status
$S | ConvertTo-Json -Depth 6 | Set-Content -Path $StatusFile -Encoding UTF8
Log "===== KEEPER RUN END  ok=$($S.ok) ====="
