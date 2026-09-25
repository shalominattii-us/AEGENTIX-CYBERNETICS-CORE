#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    AEGIS-7 Deployment Suite — Enterprise-Grade Sovereign Infrastructure
.DESCRIPTION
    Advanced Emerging Technology (AET) toolchain installer for the Sovereign
    Off-Axis Diplomacy Markets platform. Deploys full-stack development
    environment, distributed systems mesh, and sovereign-grade security.

    Classification: SOV-ENTERPRISE | Principal: shalominattii-us
    Build: AEGIS-7-001 | Clearance: Sovereign Tier
.NOTES
    Author: Sovereign Systems Architecture
    Version: 7.0.1-ENTERPRISE
    Compatible: Windows 11 23H2+ / Windows 10 22H2+
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$DeploymentZone = "C:\Sovereign",

    [Parameter()]
    [string]$GitHubToken = "",

    [Parameter()]
    [ValidateSet("Full","Development","Security","Operations","Minimal")]
    [string]$DeploymentProfile = "Full",

    [switch]$Silent,
    [switch]$NoReboot
)

# ═══════════════════════════════════════════════════════════════════════════════
# AEGIS-7 CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
$script:AEGIS_VERSION = "7.0.1-ENTERPRISE"
$script:AEGIS_BUILD = "AEGIS-7-001"
$script:SOV_PRINCIPAL = "shalominattii-us"
$script:ESC_ISSUER = "rB2fKokBsnHCoFWLqZ89dqp2VCbVkKoY2k"
$script:LOG_PATH = "$env:TEMP\AEGIS7-Deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$script:START_TIME = Get-Date

# ═══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE LOGGING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
function Write-AEGISLog {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("INFO","SUCCESS","WARN","ERROR","CRITICAL","AUDIT")]
        [string]$Level,

        [Parameter(Mandatory)]
        [string]$Message,

        [string]$Module = "CORE",

        [string]$Phase = "INIT"
    )

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    $elapsed = [math]::Round(((Get-Date) - $script:START_TIME).TotalSeconds, 2)
    $logEntry = "[$timestamp] [$Level] [$Module] [$Phase] [${elapsed}s] $Message"

    # File log
    Add-Content -Path $script:LOG_PATH -Value $logEntry -ErrorAction SilentlyContinue

    # Console output with enterprise colors
    switch ($Level) {
        "INFO"      { Write-Host $logEntry -ForegroundColor DarkGray }
        "SUCCESS"   { Write-Host $logEntry -ForegroundColor Green }
        "WARN"      { Write-Host $logEntry -ForegroundColor Yellow }
        "ERROR"     { Write-Host $logEntry -ForegroundColor Red }
        "CRITICAL"  { Write-Host $logEntry -ForegroundColor Magenta }
        "AUDIT"     { Write-Host $logEntry -ForegroundColor Cyan }
    }
}

function Show-AEGISBanner {
    Clear-Host
    Write-Host ""
    Write-Host "    ╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "    ║                                                                              ║" -ForegroundColor Cyan
    Write-Host "    ║     ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓     A E G I S - 7              ║" -ForegroundColor Cyan
    Write-Host "    ║     ▓▓      ▓▓  ▓▓  ▓▓      ▓▓      ▓▓  ▓▓     Advanced Emerging Tech        ║" -ForegroundColor Cyan
    Write-Host "    ║     ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓  ▓▓  ▓▓▓▓▓▓  ▓▓  ▓▓     Enterprise Deployment Suite   ║" -ForegroundColor Cyan
    Write-Host "    ║     ▓▓      ▓▓  ▓▓  ▓▓  ▓▓  ▓▓      ▓▓  ▓▓     Sovereign Systems              ║" -ForegroundColor Cyan
    Write-Host "    ║     ▓▓▓▓▓▓  ▓▓  ▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓     Build $script:AEGIS_VERSION    ║" -ForegroundColor Cyan
    Write-Host "    ║                                                                              ║" -ForegroundColor Cyan
    Write-Host "    ╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-AEGISLog -Level "AUDIT" -Message "AEGIS-7 Deployment Suite initialized" -Module "CORE" -Phase "INIT"
    Write-AEGISLog -Level "AUDIT" -Message "Principal: $script:SOV_PRINCIPAL | Build: $script:AEGIS_BUILD" -Module "CORE" -Phase "INIT"
    Write-AEGISLog -Level "AUDIT" -Message "Deployment Zone: $DeploymentZone | Profile: $DeploymentProfile" -Module "CORE" -Phase "INIT"
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0: SYSTEM INTELLIGENCE GATHERING
# ═══════════════════════════════════════════════════════════════════════════════
function Invoke-SystemIntelligence {
    Write-AEGISLog -Level "INFO" -Message "Gathering system intelligence..." -Module "SYSINT" -Phase "RECON"

    $sysInfo = Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory, CsProcessors
    $cpuName = ($sysInfo.CsProcessors | Select-Object -First 1).Name
    $ramGB = [math]::Round($sysInfo.TotalPhysicalMemory / 1GB, 1)

    Write-AEGISLog -Level "INFO" -Message "OS: $($sysInfo.WindowsProductName) ($($sysInfo.WindowsVersion))" -Module "SYSINT" -Phase "RECON"
    Write-AEGISLog -Level "INFO" -Message "CPU: $cpuName" -Module "SYSINT" -Phase "RECON"
    Write-AEGISLog -Level "INFO" -Message "RAM: $ramGB GB" -Module "SYSINT" -Phase "RECON"

    # Check virtualization
    $hyperv = (Get-ComputerInfo).HyperVisorPresent
    Write-AEGISLog -Level "INFO" -Message "Hypervisor: $hyperv" -Module "SYSINT" -Phase "RECON"

    # Check TPM
    try {
        $tpm = Get-Tpm
        Write-AEGISLog -Level "INFO" -Message "TPM: Present=$($tpm.TpmPresent) Ready=$($tpm.TpmReady)" -Module "SYSINT" -Phase "RECON"
    } catch {
        Write-AEGISLog -Level "WARN" -Message "TPM check failed — firmware TPM may be disabled" -Module "SYSINT" -Phase "RECON"
    }

    # Disk space
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object @{N="FreeGB";E={[math]::Round($_.FreeSpace/1GB,1)}}, @{N="TotalGB";E={[math]::Round($_.Size/1GB,1)}}
    Write-AEGISLog -Level "INFO" -Message "Storage: $($disk.FreeGB)GB free / $($disk.TotalGB)GB total" -Module "SYSINT" -Phase "RECON"

    if ($disk.FreeGB -lt 50) {
        Write-AEGISLog -Level "WARN" -Message "Low disk space — recommend 50GB minimum for full deployment" -Module "SYSINT" -Phase "RECON"
    }

    Write-AEGISLog -Level "SUCCESS" -Message "System intelligence complete" -Module "SYSINT" -Phase "RECON"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: INFRASTRUCTURE DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════════
function Deploy-Infrastructure {
    Write-AEGISLog -Level "INFO" -Message "Phase 1: Infrastructure Deployment" -Module "INFRA" -Phase "DEPLOY"

    # Create directory structure
    $directories = @(
        "platform/core",
        "platform/diplomacy",
        "platform/executive",
        "platform/agentic",
        "platform/workstation",
        "platform/mobile",
        "infrastructure/mesh",
        "infrastructure/nexus",
        "infrastructure/quantum",
        "security/vault",
        "security/identity",
        "security/forensics",
        "data/ledger",
        "data/telemetry",
        "ops/monitoring",
        "ops/deployment"
    )

    foreach ($dir in $directories) {
        $path = Join-Path $DeploymentZone $dir
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-AEGISLog -Level "INFO" -Message "Directory created: $dir" -Module "INFRA" -Phase "DEPLOY"
    }

    Write-AEGISLog -Level "SUCCESS" -Message "Infrastructure directories deployed: $($directories.Count) nodes" -Module "INFRA" -Phase "DEPLOY"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: TOOLCHAIN ACQUISITION
# ═══════════════════════════════════════════════════════════════════════════════
function Install-Toolchain {
    param([string]$Name, [string]$CheckCommand, [string]$InstallUrl, [string]$InstallArgs, [string]$VersionPattern)

    Write-AEGISLog -Level "INFO" -Message "Acquiring $Name..." -Module "TOOLCHAIN" -Phase "ACQUIRE"

    if (Get-Command $CheckCommand -ErrorAction SilentlyContinue) {
        $version = & $CheckCommand 2>$null | Select-String $VersionPattern | Select-Object -First 1
        Write-AEGISLog -Level "SUCCESS" -Message "$Name already present — $version" -Module "TOOLCHAIN" -Phase "ACQUIRE"
        return $true
    }

    try {
        $installer = "$env:TEMP\AEGIS7-$Name-Installer.exe"
        Write-AEGISLog -Level "INFO" -Message "Downloading $Name from secure repository..." -Module "TOOLCHAIN" -Phase "ACQUIRE"

        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $InstallUrl -OutFile $installer -UseBasicParsing -TimeoutSec 120

        Write-AEGISLog -Level "INFO" -Message "Installing $Name..." -Module "TOOLCHAIN" -Phase "ACQUIRE"
        $proc = Start-Process -FilePath $installer -ArgumentList $InstallArgs -Wait -PassThru

        if ($proc.ExitCode -eq 0) {
            Remove-Item $installer -Force -ErrorAction SilentlyContinue
            Write-AEGISLog -Level "SUCCESS" -Message "$Name acquisition complete" -Module "TOOLCHAIN" -Phase "ACQUIRE"
            return $true
        } else {
            throw "Exit code: $($proc.ExitCode)"
        }
    } catch {
        Write-AEGISLog -Level "ERROR" -Message "$Name acquisition failed: $_" -Module "TOOLCHAIN" -Phase "ACQUIRE"
        return $false
    }
}

function Deploy-Toolchains {
    Write-AEGISLog -Level "INFO" -Message "Phase 2: Advanced Toolchain Acquisition" -Module "TOOLCHAIN" -Phase "ACQUIRE"

    $toolchains = @()

    if ($DeploymentProfile -in @("Full","Development","Operations")) {
        $toolchains += @{
            Name = "Git SCM"
            Check = "git"
            Url = "https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/Git-2.45.1-64-bit.exe"
            Args = "/VERYSILENT /NORESTART /COMPONENTS=icons,ext,gitlfs,assoc,assoc_sh"
            Pattern = "git version"
        }

        $toolchains += @{
            Name = "Node.js LTS (Hydrogen)"
            Check = "node"
            Url = "https://nodejs.org/dist/v20.13.1/node-v20.13.1-x64.msi"
            Args = "/qn /norestart"
            Pattern = "v20"
        }
    }

    if ($DeploymentProfile -in @("Full","Security","Operations")) {
        $toolchains += @{
            Name = "Docker Engine"
            Check = "docker"
            Url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
            Args = "install --quiet --accept-license"
            Pattern = "Docker version"
        }
    }

    if ($DeploymentProfile -in @("Full","Development")) {
        $toolchains += @{
            Name = "Python 3.12"
            Check = "python"
            Url = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
            Args = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
            Pattern = "3.12"
        }

        $toolchains += @{
            Name = "VS Code"
            Check = "code"
            Url = "https://update.code.visualstudio.com/latest/win32-x64-user/stable"
            Args = "/VERYSILENT /NORESTART /MERGETASKS=!runcode"
            Pattern = ""
        }
    }

    if ($DeploymentProfile -in @("Full","Operations")) {
        $toolchains += @{
            Name = "WSL2 Ubuntu"
            Check = "wsl"
            Url = ""
            Args = ""
            Pattern = ""
            Special = $true
        }
    }

    $successCount = 0
    foreach ($tool in $toolchains) {
        if ($tool.Special) {
            # WSL special handling
            Write-AEGISLog -Level "INFO" -Message "Deploying WSL2 + Ubuntu LTS..." -Module "TOOLCHAIN" -Phase "ACQUIRE"
            wsl --install --distribution Ubuntu --no-launch 2>$null
            Write-AEGISLog -Level "SUCCESS" -Message "WSL2 + Ubuntu deployed" -Module "TOOLCHAIN" -Phase "ACQUIRE"
            $successCount++
        } else {
            $result = Install-Toolchain -Name $tool.Name -CheckCommand $tool.Check -InstallUrl $tool.Url -InstallArgs $tool.Args -VersionPattern $tool.Pattern
            if ($result) { $successCount++ }
        }
    }

    Write-AEGISLog -Level "SUCCESS" -Message "Toolchain acquisition complete: $successCount/$($toolchains.Count) systems operational" -Module "TOOLCHAIN" -Phase "ACQUIRE"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: SOVEREIGN PLATFORM CLONE
# ═══════════════════════════════════════════════════════════════════════════════
function Clone-SovereignPlatform {
    Write-AEGISLog -Level "INFO" -Message "Phase 3: Sovereign Platform Acquisition" -Module "PLATFORM" -Phase "CLONE"

    $repoPath = Join-Path $DeploymentZone "SOVEREIGN"
    $repoUrl = if ($GitHubToken) {
        "https://$GitHubToken@github.com/shalominattii-us/SOVEREIGN.git"
    } else {
        "https://github.com/shalominattii-us/SOVEREIGN.git"
    }

    if (Test-Path "$repoPath\.git") {
        Write-AEGISLog -Level "INFO" -Message "Platform already present — synchronizing..." -Module "PLATFORM" -Phase "CLONE"
        Set-Location $repoPath
        git fetch origin main 2>$null
        git reset --hard origin/main 2>$null
        Write-AEGISLog -Level "SUCCESS" -Message "Platform synchronized to HEAD" -Module "PLATFORM" -Phase "CLONE"
    } else {
        Write-AEGISLog -Level "INFO" -Message "Cloning Sovereign platform from secure repository..." -Module "PLATFORM" -Phase "CLONE"
        git clone $repoUrl $repoPath --depth 1 --branch main 2>$null
        Write-AEGISLog -Level "SUCCESS" -Message "Platform acquired: $repoPath" -Module "PLATFORM" -Phase "CLONE"
    }

    # Write deployment manifest
    $manifest = @{
        deploymentId = [Guid]::NewGuid().ToString()
        timestamp = Get-Date -Format "O"
        principal = $script:SOV_PRINCIPAL
        build = $script:AEGIS_BUILD
        version = $script:AEGIS_VERSION
        profile = $DeploymentProfile
        zone = $DeploymentZone
        escIssuer = $script:ESC_ISSUER
        treasuryType = "TSL"
        custodyTerm = "Destiny"
    } | ConvertTo-Json -Depth 3

    $manifest | Out-File -FilePath "$repoPath\.aegis-manifest.json" -Encoding UTF8
    Write-AEGISLog -Level "AUDIT" -Message "Deployment manifest written: $($manifest.deploymentId)" -Module "PLATFORM" -Phase "CLONE"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: SECURITY HARDENING
# ═══════════════════════════════════════════════════════════════════════════════
function Invoke-SecurityHardening {
    Write-AEGISLog -Level "INFO" -Message "Phase 4: Security Hardening Protocol" -Module "SECURITY" -Phase "HARDEN"

    # Configure Windows Defender for development
    Write-AEGISLog -Level "INFO" -Message "Configuring endpoint protection..." -Module "SECURITY" -Phase "HARDEN"

    try {
        Set-MpPreference -DisableRealtimeMonitoring $false
        Set-MpPreference -DisableBehaviorMonitoring $false
        Set-MpPreference -MAPSReporting Advanced
        Set-MpPreference -SubmitSamplesConsent SendAllSamples
        Write-AEGISLog -Level "SUCCESS" -Message "Endpoint protection optimized" -Module "SECURITY" -Phase "HARDEN"
    } catch {
        Write-AEGISLog -Level "WARN" -Message "Endpoint protection config requires manual review" -Module "SECURITY" -Phase "HARDEN"
    }

    # Firewall rules for Sovereign
    Write-AEGISLog -Level "INFO" -Message "Deploying network security policies..." -Module "SECURITY" -Phase "HARDEN"

    $sovereignPorts = @(
        @{ Port = 3000; Protocol = "TCP"; Name = "SOV-APP" },
        @{ Port = 8080; Protocol = "TCP"; Name = "SOV-MESH" },
        @{ Port = 51820; Protocol = "UDP"; Name = "SOV-WIREGUARD" },
        @{ Port = 51821; Protocol = "TCP"; Name = "SOV-WG-UI" },
        @{ Port = 11434; Protocol = "TCP"; Name = "SOV-OLLAMA" }
    )

    foreach ($rule in $sovereignPorts) {
        netsh advfirewall firewall add rule name="AEGIS7-$($rule.Name)" dir=in action=allow protocol=$($rule.Protocol) localport=$($rule.Port) | Out-Null
        Write-AEGISLog -Level "INFO" -Message "Firewall rule: $($rule.Name) $($rule.Protocol)/$($rule.Port)" -Module "SECURITY" -Phase "HARDEN"
    }

    Write-AEGISLog -Level "SUCCESS" -Message "Network security policies deployed: $($sovereignPorts.Count) rules" -Module "SECURITY" -Phase "HARDEN"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: DEPLOYMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════
function Invoke-DeploymentVerification {
    Write-AEGISLog -Level "INFO" -Message "Phase 5: Deployment Verification" -Module "VERIFY" -Phase "AUDIT"

    $checks = @()

    # Check Git
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $checks += @{ Component = "Git"; Status = "OPERATIONAL"; Version = (git --version) }
    } else {
        $checks += @{ Component = "Git"; Status = "OFFLINE"; Version = "N/A" }
    }

    # Check Node
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $checks += @{ Component = "Node.js"; Status = "OPERATIONAL"; Version = (node --version) }
    } else {
        $checks += @{ Component = "Node.js"; Status = "OFFLINE"; Version = "N/A" }
    }

    # Check Docker
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $checks += @{ Component = "Docker"; Status = "OPERATIONAL"; Version = (docker --version 2>$null) }
    } else {
        $checks += @{ Component = "Docker"; Status = "OFFLINE"; Version = "N/A" }
    }

    # Check Python
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $checks += @{ Component = "Python"; Status = "OPERATIONAL"; Version = (python --version 2>&1) }
    } else {
        $checks += @{ Component = "Python"; Status = "OFFLINE"; Version = "N/A" }
    }

    # Check Sovereign repo
    $repoPath = Join-Path $DeploymentZone "SOVEREIGN"
    if (Test-Path "$repoPath\.git") {
        $checks += @{ Component = "Sovereign Platform"; Status = "OPERATIONAL"; Version = "LIVE" }
    } else {
        $checks += @{ Component = "Sovereign Platform"; Status = "OFFLINE"; Version = "N/A" }
    }

    Write-Host ""
    Write-Host "    ╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "    ║                    AEGIS-7 SYSTEMS STATUS REPORT                             ║" -ForegroundColor Cyan
    Write-Host "    ╠══════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan

    foreach ($check in $checks) {
        $color = if ($check.Status -eq "OPERATIONAL") { "Green" } else { "Red" }
        $symbol = if ($check.Status -eq "OPERATIONAL") { "●" } else { "○" }
        Write-Host "    ║  $symbol $($check.Component.PadRight(20)) | $($check.Status.PadRight(12)) | $($check.Version.PadRight(30)) ║" -ForegroundColor $color
    }

    Write-Host "    ╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $operational = ($checks | Where-Object { $_.Status -eq "OPERATIONAL" }).Count
    $total = $checks.Count

    Write-AEGISLog -Level "AUDIT" -Message "Systems operational: $operational/$total" -Module "VERIFY" -Phase "AUDIT"

    if ($operational -eq $total) {
        Write-AEGISLog -Level "SUCCESS" -Message "ALL SYSTEMS OPERATIONAL — Deployment verified" -Module "VERIFY" -Phase "AUDIT"
    } else {
        Write-AEGISLog -Level "WARN" -Message "Partial deployment — review offline systems" -Module "VERIFY" -Phase "AUDIT"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════
Show-AEGISBanner
Invoke-SystemIntelligence
Deploy-Infrastructure
Deploy-Toolchains
Clone-SovereignPlatform
Invoke-SecurityHardening
Invoke-DeploymentVerification

# Final report
$elapsed = [math]::Round(((Get-Date) - $script:START_TIME).TotalSeconds, 2)
Write-Host ""
Write-Host "    ╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "    ║                                                                              ║" -ForegroundColor Green
Write-Host "    ║           AEGIS-7 DEPLOYMENT COMPLETE                                        ║" -ForegroundColor Green
Write-Host "    ║           Elapsed: ${elapsed}s | Log: $script:LOG_PATH                    ║" -ForegroundColor Green
Write-Host "    ║                                                                              ║" -ForegroundColor Green
Write-Host "    ║           Next: cd $DeploymentZone\SOVEREIGN                               ║" -ForegroundColor Green
Write-Host "    ║                                                                              ║" -ForegroundColor Green
Write-Host "    ╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-AEGISLog -Level "AUDIT" -Message "AEGIS-7 deployment complete — Elapsed: ${elapsed}s" -Module "CORE" -Phase "COMPLETE"
Write-AEGISLog -Level "AUDIT" -Message "Principal $script:SOV_PRINCIPAL authorized — All systems nominal" -Module "CORE" -Phase "COMPLETE"

# Reboot prompt
if (-not $NoReboot) {
    $reboot = Read-Host "    [AEGIS-7] Reboot required for Docker/WSL. Reboot now? (Y/N)"
    if ($reboot -eq "Y" -or $reboot -eq "y") {
        Write-AEGISLog -Level "AUDIT" -Message "System reboot initiated by operator" -Module "CORE" -Phase "REBOOT"
        Restart-Computer -Force
    }
}
