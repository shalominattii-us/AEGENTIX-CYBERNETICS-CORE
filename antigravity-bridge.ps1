# antigravity-bridge.ps1 — talk to the running Google Antigravity 2.0 desktop app from PowerShell
# Usage:  . C:\Aegentix\antigravity-bridge.ps1
#         ag-meta <conversationId>
#         ag-send <conversationId> "message"
#         ag-new  "prompt" [-Model flash|pro|flash_lite] [-Title "..."]
# Auth (port + CSRF token) is read live from the language_server.exe process, so it survives app restarts.

$script:AgLS = "$env:LOCALAPPDATA\Programs\antigravity\resources\bin\language_server.exe"

function Get-AgAuth {
    $proc = Get-CimInstance Win32_Process -Filter "Name='language_server.exe'" | Select-Object -First 1
    if (-not $proc) { throw "Antigravity is not running (no language_server.exe). Open the Antigravity app first." }
    $cmd = $proc.CommandLine
    if ($cmd -notmatch '--csrf_token\s+([0-9a-f-]{36})') { throw "CSRF token not found on language_server command line." }
    $token = $Matches[1]
    $ports = (netstat -ano | Select-String "127\.0\.0\.1:(\d+)\s+0\.0\.0\.0:0\s+LISTENING\s+$($proc.ProcessId)\s*$" |
              ForEach-Object { [int]$_.Matches[0].Groups[1].Value }) | Sort-Object
    if ($ports.Count -lt 2) { throw "Could not find the language_server gRPC port (found: $($ports -join ','))." }
    # Second listening port is the authenticated gRPC endpoint
    return @{ Address = "127.0.0.1:$($ports[1])"; Token = $token }
}

function Invoke-AgentApi {
    param([Parameter(ValueFromRemainingArguments)][string[]]$Args)
    $a = Get-AgAuth
    $env:ANTIGRAVITY_LS_ADDRESS = $a.Address
    $env:ANTIGRAVITY_CSRF_TOKEN = $a.Token
    & $script:AgLS agentapi @Args
}

function ag-meta { param([Parameter(Mandatory)][string]$ConversationId)
    Invoke-AgentApi get-conversation-metadata $ConversationId }

function ag-send { param([Parameter(Mandatory)][string]$ConversationId,
                         [Parameter(Mandatory)][string]$Message,
                         [string]$Title = "From Aegentix")
    Invoke-AgentApi send-message "--title=$Title" $ConversationId $Message }

function ag-new { param([Parameter(Mandatory)][string]$Prompt,
                        [ValidateSet('flash_lite','flash','pro')][string]$Model = 'flash',
                        [string]$Title = "Aegentix task")
    Invoke-AgentApi new-conversation "--model=$Model" "--title=$Title" $Prompt }

Write-Host "🪐 Antigravity bridge loaded: ag-meta, ag-send, ag-new" -ForegroundColor Cyan
