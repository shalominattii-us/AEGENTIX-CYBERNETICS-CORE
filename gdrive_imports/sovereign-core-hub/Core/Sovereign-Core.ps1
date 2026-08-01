$rootBackend = "C:\sovereign-prime"
$unityRoot   = "C:\EagleShieldUnity"
$baseDir     = "C:\Sovereign"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "FATAL: Missing dependency: $Name" -ForegroundColor Red
        exit 1
    }
}

function Stop-ContainerSafe {
    param([string]$Name)
    $exists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $Name }
    if ($exists) {
        Write-Host "Stopping container $Name..." -ForegroundColor Yellow
        docker stop $Name | Out-Null
        docker rm   $Name | Out-Null
    }
}

function Init-EnvCore {
    Require-Command docker
    if (-not (Test-Path $baseDir)) {
        New-Item -ItemType Directory -Force -Path $baseDir | Out-Null
    }
}

function Clean-StateCore {
    Stop-ContainerSafe "sovereign-prime"
    if (Test-Path $rootBackend) { Write-Host "Removing $rootBackend..." -ForegroundColor Yellow; Remove-Item -Recurse -Force $rootBackend }
    if (Test-Path $unityRoot)   { Write-Host "Removing $unityRoot..."   -ForegroundColor Yellow; Remove-Item -Recurse -Force $unityRoot }
}

function CORE-BuildBackend {
    Write-Host ">>> TODO: Paste your existing backend generator body here (sovereign-prime) <<<" -ForegroundColor Yellow
}

function CORE-BuildUnity {
    Write-Host ">>> TODO: Paste your existing Unity generator body here (EagleShieldUnity) <<<" -ForegroundColor Yellow
}

function CORE-BringUpSovereign {
    Write-Host "Building Sovereign Prime Docker image..." -ForegroundColor Yellow
    cd $rootBackend
    docker compose up -d --build
}

function CORE-ShortcutsAndVersion {
    $desktop   = [Environment]::GetFolderPath("Desktop")
    $shortcut1 = Join-Path $desktop "Sovereign Console.url"
    $shortcut2 = Join-Path $desktop "EagleShieldUnity.url"

@"
[InternetShortcut]
URL=http://localhost:8004/crown-omega
"@ | Set-Content -Encoding ASCII $shortcut1

@"
[InternetShortcut]
URL=file:///$unityRoot
"@ | Set-Content -Encoding ASCII $shortcut2

    $version = @{
        name    = "sovereign-stack"
        version = "1.0.0"
        build   = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    $version | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $rootBackend "installer-version.json")
}
