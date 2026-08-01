# ==========================================================
#   SOVEREIGN OS‑12.1 — CLEAN PATCHER (NO JS IN POWERSHELL)
# ==========================================================

$ErrorActionPreference = "Stop"
$root = "C:\Sovereign"

function Add-Patch {
    param([string]$File, [string]$Patch)

    if (-not (Test-Path $File)) {
        Write-Host "[OS12.1][PATCH] Missing $File" -ForegroundColor Yellow
        return
    }

    $content = Get-Content $File -Raw
    if ($content -match "OS12.1_PATCHED") {
        Write-Host "[OS12.1][PATCH] Already patched: $File" -ForegroundColor DarkGreen
        return
    }

    $patched = $content + "`r`n// OS12.1_PATCHED`r`n" + $Patch
    Set-Content -Path $File -Value $patched -Encoding UTF8

    Write-Host "[OS12.1][PATCH] Patched: $File" -ForegroundColor Cyan
}

# -------------------------
# AEGENTIS VR
# -------------------------
$vrFile = "$root\aegentis-vr-backend\vr-server.js"
$vrPatch = @"
// OS12.1_PATCH
const { detectShell } = require('../os12.1/os12-autoShellDetect');
const { attachVrMetrics } = require('../os12.1/os12-vrMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

detectShell();
attachVrMetrics({ wss, app, label: 'Aegentis VR' });
registerRuntime('aegentis-vr', {
  port: 7777,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
"@
Add-Patch $vrFile $vrPatch

# -------------------------
# DASHBOARD
# -------------------------
$dashFile = "$root\sovereign-dashboard-react\server.js"
$dashPatch = @"
// OS12.1_PATCH
const { initPortalFusion } = require('../os12.1/os12-portalFusion');
const { attachSystemMetrics } = require('../os12.1/os12-systemMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

initPortalFusion({ app });
attachSystemMetrics(app, { label: 'dashboard' });
registerRuntime('dashboard', {
  port: 3000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
"@
Add-Patch $dashFile $dashPatch

# -------------------------
# DESTINY
# -------------------------
$destFile = "$root\destiny-custody-bridge\index.js"
$destPatch = @"
// OS12.1_PATCH
const { attachSystemMetrics } = require('../os12.1/os12-systemMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

attachSystemMetrics(app, { label: 'destiny' });
registerRuntime('destiny', {
  port: 9229,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
"@
Add-Patch $destFile $destPatch

# -------------------------
# TSL LEDGER
# -------------------------
$tslFile = "$root\tsl-ledger-interface\server.js"
$tslPatch = @"
// OS12.1_PATCH
const { attachSystemMetrics } = require('../os12.1/os12-systemMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

attachSystemMetrics(app, { label: 'tsl-ledger' });
registerRuntime('tsl-ledger', {
  port: 9000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
"@
Add-Patch $tslFile $tslPatch

# -------------------------
# AGENTIC (optional)
# -------------------------
$agentFile = "$root\agentic-ai-orchestrator\gateway.js"
if (Test-Path $agentFile) {
    $agentPatch = @"
// OS12.1_PATCH
const { attachSystemMetrics } = require('../os12.1/os12-systemMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

attachSystemMetrics(app, { label: 'agentic-ai' });
registerRuntime('agentic-ai', {
  port: 8844,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
"@
    Add-Patch $agentFile $agentPatch
}

Write-Host "🚀 OS‑12.1 PATCH COMPLETE" -ForegroundColor Green
