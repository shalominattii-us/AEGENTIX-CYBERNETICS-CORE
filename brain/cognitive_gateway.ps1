param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "status",
        "intent",
        "plan",
        "models"
    )]
    [string]$Operation,

    [string]$Source = "JARVIS",

    [string]$Intent,

    [string]$Objective
)

$ErrorActionPreference = "Stop"

$Root = "C:\aegentix"
$Brain = Join-Path $Root "brain"
$Runtime = Join-Path $Root "runtime"
$StateFile = Join-Path $Runtime "state.json"
$EventsDir = Join-Path $Runtime "events"

$KernelStateCore = Join-Path $Root "Kernel\State\state-core.ps1"
$KernelStateRuntime = Join-Path $Root "Kernel\State\state-runtime.ps1"
$KernelStateOps = Join-Path $Root "Kernel\State\state-ops.ps1"

function Fail-Closed {
    param([string]$Message)

    $result = [ordered]@{
        ok = $false
        mode = "FAIL_CLOSED"
        error = $Message
    }

    $result | ConvertTo-Json -Depth 20
    exit 2
}

function Get-CanonicalState {

    if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) {
        Fail-Closed "Canonical runtime state file does not exist."
    }

    try {
        return Get-Content `
            -LiteralPath $StateFile `
            -Raw `
            -ErrorAction Stop |
            ConvertFrom-Json `
            -ErrorAction Stop
    }
    catch {
        Fail-Closed "Canonical runtime state is not valid JSON."
    }
}

function Get-EventHead {

    if (-not (Test-Path -LiteralPath $EventsDir -PathType Container)) {
        return $null
    }

    $files = @(
        Get-ChildItem `
            -LiteralPath $EventsDir `
            -File `
            -Filter "*.jsonl" `
            -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc
    )

    if ($files.Count -eq 0) {
        return $null
    }

    $lastFile = $files[-1]

    $lines = @(
        Get-Content `
            -LiteralPath $lastFile.FullName `
            -ErrorAction SilentlyContinue
    )

    if ($lines.Count -eq 0) {
        return $null
    }

    try {
        return $lines[-1] | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-Governance {

    $path = Join-Path `
        $Root `
        "governance\policies\default.json"

    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Fail-Closed "Governance policy is missing."
    }

    try {
        return Get-Content `
            -LiteralPath $path `
            -Raw |
            ConvertFrom-Json
    }
    catch {
        Fail-Closed "Governance policy is invalid JSON."
    }
}

function New-IntentEvent {

    param(
        [string]$EventSource,
        [string]$EventIntent,
        [string]$EventObjective
    )

    $timestamp = [DateTimeOffset]::UtcNow

    $payload = [ordered]@{
        intent = $EventIntent
        objective = $EventObjective
        source = $EventSource
        authority = "COGNITIVE"
        action = "REQUEST_ONLY"
    }

    $canonical = (
        $payload |
        ConvertTo-Json -Compress -Depth 20
    )

    $sha = [System.Security.Cryptography.SHA256]::Create()

    try {
        $hashBytes = $sha.ComputeHash(
            [System.Text.Encoding]::UTF8.GetBytes($canonical)
        )

        $hash = (
            [System.BitConverter]::ToString($hashBytes)
        ).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }

    return [ordered]@{
        event_id = [guid]::NewGuid().ToString()
        event_type = "COGNITIVE_INTENT"
        source = $EventSource
        timestamp = $timestamp.ToString("o")
        payload = $payload
        sha256 = $hash
    }
}

switch ($Operation) {

    "status" {

        $state = Get-CanonicalState
        $governance = Get-Governance
        $head = Get-EventHead

        [ordered]@{
            ok = $true
            mode = "OBSERVE"
            invariant = "Event first. State second."
            direct_state_mutation = $false
            external_actions = "FAIL_CLOSED"
            state = $state
            event_head = $head
            governance = $governance
        } |
        ConvertTo-Json -Depth 30

        exit 0
    }

    "models" {

        $registry = Join-Path `
            $Brain `
            "router\model_registry.json"

        if (-not (Test-Path -LiteralPath $registry -PathType Leaf)) {
            Fail-Closed "Model registry is missing."
        }

        try {
            $models = Get-Content `
                -LiteralPath $registry `
                -Raw |
                ConvertFrom-Json `
                -ErrorAction Stop
        }
        catch {
            Fail-Closed "Model registry is invalid JSON."
        }

        [ordered]@{
            ok = $true
            registry = $models
        } |
        ConvertTo-Json -Depth 30

        exit 0
    }

    "plan" {

        $planner = Join-Path `
            $Brain `
            "jarvis\planner.py"

        if (-not (Test-Path -LiteralPath $planner -PathType Leaf)) {
            Fail-Closed "JARVIS planner is missing."
        }

        [ordered]@{
            ok = $true
            operation = "plan"
            planner = $planner
            authority = "JARVIS_COGNITIVE_ONLY"
            execution = "DISABLED_AT_GATEWAY"
            objective = $Objective
        } |
        ConvertTo-Json -Depth 20

        exit 0
    }

    "intent" {

        if ([string]::IsNullOrWhiteSpace($Intent)) {
            Fail-Closed "Intent cannot be empty."
        }

        $event = New-IntentEvent `
            -EventSource $Source `
            -EventIntent $Intent `
            -EventObjective $Objective

        # ----------------------------------------------------
        # CRITICAL AUTHORITY RULE
        #
        # This gateway does NOT write runtime/state.json.
        # It does NOT directly invoke arbitrary kernel mutation.
        #
        # The cognitive layer produces an intent artifact.
        # The existing kernel remains authoritative.
        # ----------------------------------------------------

        New-Item `
            -ItemType Directory `
            -Path $EventsDir `
            -Force |
            Out-Null

        $eventFile = Join-Path `
            $EventsDir `
            ("cognitive_" + (Get-Date -Format "yyyyMMdd") + ".jsonl")

        $line = $event | ConvertTo-Json -Compress -Depth 30

        Add-Content `
            -LiteralPath $eventFile `
            -Value $line `
            -Encoding UTF8

        [ordered]@{
            ok = $true
            accepted = $true
            mode = "REQUEST_ONLY"
            event = $event
            event_file = $eventFile
            invariant = "Event first. State second."
            state_mutation = $false
            external_action = "FAIL_CLOSED"
        } |
        ConvertTo-Json -Depth 30

        exit 0
    }
}