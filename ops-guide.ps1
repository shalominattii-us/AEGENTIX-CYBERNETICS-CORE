#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Aegentix Production Stack Operations Guide
    Unified autonomous security cluster with behavioral threat detection

.DESCRIPTION
    This document outlines operational procedures, diagnostics, and maintenance
    for the complete Aegentix production environment.

#>

$ErrorActionPreference = "Stop"

# =========================================================================
# STACK OVERVIEW
# =========================================================================
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         AEGENTIX PRODUCTION STACK - OPERATIONS GUIDE           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "COMPONENTS:" -ForegroundColor Yellow
Write-Host "  ✓ Core Routing: NATS (4222), Aegentis Router (8080)"
Write-Host "  ✓ Security: 5 Autonomous Agents + Telemetry Engine"
Write-Host "  ✓ Observability: Prometheus (9090), Grafana (3001), Alertmanager (9093)"
Write-Host "  ✓ Logging: Elasticsearch (9200), Kibana (5601), Filebeat"
Write-Host "  ✓ Legacy: Operator Console (3000), Skill Registry, Aegentis Twin"

# =========================================================================
# 1. STARTUP
# =========================================================================
Write-Host ""
Write-Host "━━━ 1. STARTUP ━━━" -ForegroundColor Green

function Start-AegentixStack {
    Write-Host "Starting production stack..." -ForegroundColor Cyan
    docker compose -f docker-compose.production.yml up -d --pull always
    Write-Host "✓ Stack started" -ForegroundColor Green
    Start-Sleep -Seconds 10
    Show-StackStatus
}

# =========================================================================
# 2. STATUS & HEALTH
# =========================================================================
function Show-StackStatus {
    Write-Host ""
    Write-Host "━━━ STACK HEALTH STATUS ━━━" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "aegentix|nats|router|console" }
}

function Show-DetailedHealth {
    Write-Host ""
    Write-Host "━━━ DETAILED HEALTH CHECKS ━━━" -ForegroundColor Cyan
    
    $services = @(
        "nats",
        "aegentis-router",
        "agent-monitoring",
        "agent-incident-response",
        "agent-healing",
        "agent-autoscaling",
        "agent-deployment",
        "prometheus",
        "alertmanager",
        "grafana",
        "elasticsearch",
        "kibana",
        "aegentix-telemetry-engine"
    )
    
    foreach ($svc in $services) {
        $status = docker ps --filter "name=$svc" --format "{{.Status}}"
        if ($status -match "Up") {
            Write-Host "  ✓ $svc — $status" -ForegroundColor Green
        } elseif ($status -match "Restarting|Exited") {
            Write-Host "  ✗ $svc — $status" -ForegroundColor Red
        } else {
            Write-Host "  ? $svc — Not running" -ForegroundColor Yellow
        }
    }
}

# =========================================================================
# 3. LOGS & DIAGNOSTICS
# =========================================================================
function Show-AgentLogs {
    param([string]$Agent = "agent-monitoring")
    Write-Host ""
    Write-Host "━━━ LOGS: $Agent ━━━" -ForegroundColor Cyan
    docker logs --tail 50 "aegentix-$Agent" 2>&1
}

function Show-SecurityLogs {
    Write-Host ""
    Write-Host "━━━ SECURITY ENGINE LOGS ━━━" -ForegroundColor Cyan
    docker logs --tail 30 aegentix-telemetry-engine 2>&1
}

function Show-AlertmanagerAlerts {
    Write-Host ""
    Write-Host "━━━ ACTIVE ALERTS ━━━" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "http://localhost:9093/api/v1/alerts" -UseBasicParsing | ConvertFrom-Json | Select-Object -ExpandProperty data | Format-Table status, @{N="alert";E={$_.labels.alertname}}, @{N="severity";E={$_.labels.severity}}
}

function Show-PrometheusRules {
    Write-Host ""
    Write-Host "━━━ PROMETHEUS ALERT RULES ━━━" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "http://localhost:9090/api/v1/rules" -UseBasicParsing | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty groups | Format-Table -Property name, @{N="rules";E={$_.rules.Count}}
}

# =========================================================================
# 4. SHUTDOWN
# =========================================================================
function Stop-AegentixStack {
    Write-Host ""
    Write-Host "Stopping production stack..." -ForegroundColor Yellow
    docker compose -f docker-compose.production.yml down
    Write-Host "✓ Stack stopped" -ForegroundColor Green
}

# =========================================================================
# 5. MAINTENANCE
# =========================================================================
function Restart-Service {
    param([string]$Service)
    Write-Host "Restarting $Service..." -ForegroundColor Yellow
    docker compose -f docker-compose.production.yml restart $Service
    Write-Host "✓ Restarted" -ForegroundColor Green
}

function Rebuild-Agents {
    Write-Host "Rebuilding agent images..." -ForegroundColor Yellow
    docker compose -f docker-compose.production.yml build --no-cache agent-monitoring agent-incident-response agent-healing agent-autoscaling agent-deployment
    Write-Host "✓ Rebuild complete" -ForegroundColor Green
}

# =========================================================================
# 6. QUICK ACCESS URLS
# =========================================================================
function Show-AccessPoints {
    Write-Host ""
    Write-Host "━━━ ACCESS POINTS ━━━" -ForegroundColor Cyan
    Write-Host "  Prometheus:         http://localhost:9090"
    Write-Host "  Prometheus Alerts:  http://localhost:9090/alerts"
    Write-Host "  Grafana:            http://localhost:3001 (admin/admin)"
    Write-Host "  Alertmanager:       http://localhost:9093"
    Write-Host "  Kibana:             http://localhost:5601"
    Write-Host "  Operator Console:   http://localhost:3000"
    Write-Host "  NATS Monitor:       http://localhost:8222"
    Write-Host "  Router Health:      http://localhost:8080/health"
}

# =========================================================================
# 7. MENU
# =========================================================================
function Show-Menu {
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  1. Start stack"
    Write-Host "  2. Show status"
    Write-Host "  3. Show detailed health"
    Write-Host "  4. View logs (agent-monitoring)"
    Write-Host "  5. View security logs"
    Write-Host "  6. Show alerts"
    Write-Host "  7. Show Prometheus rules"
    Write-Host "  8. Restart service"
    Write-Host "  9. Show access points"
    Write-Host "  0. Exit"
}

# =========================================================================
# MAIN
# =========================================================================
if ($args.Count -eq 0) {
    Show-StackStatus
    Show-AccessPoints
} else {
    switch ($args[0]) {
        "start" { Start-AegentixStack }
        "status" { Show-StackStatus }
        "health" { Show-DetailedHealth }
        "logs" { Show-AgentLogs }
        "security" { Show-SecurityLogs }
        "alerts" { Show-AlertmanagerAlerts }
        "rules" { Show-PrometheusRules }
        "access" { Show-AccessPoints }
        "stop" { Stop-AegentixStack }
        default { 
            Write-Host "Usage: ./ops-guide.ps1 [start|status|health|logs|security|alerts|rules|access|stop]"
            Show-AccessPoints
        }
    }
}
