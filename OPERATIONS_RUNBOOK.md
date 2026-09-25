# AEGENTIX UNIFIED OPERATIONS REPOSITORY
# Master Configuration & Runbooks

## QUICK START

```powershell
# Launch Unified Operations Center
.\uoc.ps1 -Operation dashboard

# Common operations
.\uoc.ps1 -Operation status      # Check stack status
.\uoc.ps1 -Operation start       # Start production stack
.\uoc.ps1 -Operation stop        # Stop production stack
.\uoc.ps1 -Operation health      # Check agent health
.\uoc.ps1 -Operation agents      # View all 5 agents
.\uoc.ps1 -Operation blockchain  # Blockchain status
.\uoc.ps1 -Operation sovereign   # Ledger status
```

---

## PRODUCTION STACK ARCHITECTURE

### Core Infrastructure
- **NATS Messaging**: Port 4222 (event bus for all services)
- **Aegentis Router**: Port 8080 (API/WebSocket gateway)
- **Prometheus**: Port 9090 (metrics collection & alerting)
- **Grafana**: Port 3001 (dashboard visualization)
- **Alertmanager**: Port 9093 (alert routing)
- **Elasticsearch**: Port 9200 (log storage)
- **Kibana**: Port 5601 (log visualization)

### Autonomous Agents (5/5 - All Healthy)
1. **Monitoring Agent** — Real-time system observation
2. **Incident Response Agent** — Automated threat response
3. **Healing Agent** — Self-repair mechanisms
4. **Autoscaling Agent** — Dynamic resource management
5. **Deployment Agent** — Autonomous deployment orchestration

### Threat Detection Layer
- **Falco**: 8 behavioral rules (kernel syscall monitoring)
- **Telemetry Engine**: 1699 CISA KEV feeds active
- **Prometheus Rules**: 14 anomaly detection rules
- **AppArmor**: Container isolation + capability dropping

### Blockchain Infrastructure
- **MinimalNodes Registry**: 200+ chains (Bitcoin, Ethereum, Solana, etc.)
- **Node Infrastructure**: omnicyberdex_master.py, local_node.py
- **Reward Tracking**: Autonomous incentive mechanism

### SovereignSystem Integration
- **Autonomous Ledger**: 5055+ items
- **RAG Pipeline**: anythingllm_ingest_queue
- **LLM Models**: Ollama inference
- **Workflow Execution**: Autonomous state management

---

## OPERATIONAL RUNBOOKS

### 1. DAILY OPERATIONS

#### Morning Check (09:00)
```powershell
# Check all systems operational
.\uoc.ps1 -Operation dashboard

# Review overnight alerts
curl -s http://localhost:9093/api/v1/alerts | ConvertFrom-Json

# Verify blockchain nodes
.\uoc.ps1 -Operation blockchain

# Check storage sync
.\uoc.ps1 -Operation backup
```

#### Continuous Monitoring
```powershell
# Real-time agent health
watch -n 5 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# Prometheus rules evaluation
curl -s http://localhost:9090/api/v1/rules | ConvertFrom-Json

# Threat detection logs
docker logs -f aegentix-telemetry-engine
```

### 2. INCIDENT RESPONSE

#### Security Alert Detected
```powershell
# 1. Freeze logs
docker logs aegentix-agent-incident-response > incident_$(Get-Date -f yyyyMMdd_HHmmss).log

# 2. Check affected agent
docker logs <agent-name> --tail 100

# 3. View alert context
curl -s http://localhost:9093/api/v1/alerts?group_by=severity

# 4. Trigger healing if needed
docker exec <agent-name> /opt/heal.sh

# 5. Document in ledger
# (SovereignSystem autonomous logging)
```

#### Container Restart Required
```powershell
# Graceful restart
.\uoc.ps1 -Operation restart

# Single service restart
docker compose -f docker-compose.production.yml restart <service-name>

# Verify recovery
.\uoc.ps1 -Operation health
```

### 3. SCALING OPERATIONS

#### Add Blockchain Chain
```powershell
# 1. Update MinimalNodes/nodes.json
$newChain = @{
    "chain" = "new-chain"
    "status" = "active"
    "type" = "minimal"
    "blocks" = 0
    "rewards" = 0.0
}

# 2. Restart nodes
python C:\BlockchainData\local_node.py
```

#### Scale Autonomous Agents
```powershell
# Increase agent instances via docker-compose.production.yml
# Update replicas or add new service definitions
# Redeploy:
docker compose -f docker-compose.production.yml up -d --scale <agent>=N
```

### 4. BACKUP & RECOVERY

#### Full Backup Procedure
```powershell
# 1. Export logs
docker logs aegentix-telemetry-engine > backup_telemetry_$(Get-Date -f yyyyMMdd).log

# 2. Backup ledger
Copy-Item -Path "C:\SovereignSystem\ledger" -Destination "G:\My Drive\FullDeviceBackup\ledger_backup_$(Get-Date -f yyyyMMdd)" -Recurse

# 3. Export Prometheus metrics
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=up" -OutFile "backup_metrics_$(Get-Date -f yyyyMMdd).json"

# 4. Sync to Google Drive
# (Automatic via G: drive sync)
```

#### Recovery Procedure
```powershell
# 1. Stop stack
.\uoc.ps1 -Operation stop

# 2. Restore from backup
Copy-Item -Path "G:\My Drive\FullDeviceBackup\*" -Destination "C:\Aegentix" -Recurse -Force

# 3. Rebuild ledger
Copy-Item -Path "G:\My Drive\FullDeviceBackup\ledger_backup_*\*" -Destination "C:\SovereignSystem\ledger" -Recurse -Force

# 4. Restart
.\uoc.ps1 -Operation start

# 5. Verify
.\uoc.ps1 -Operation health
```

---

## SERVICE ENDPOINTS & DASHBOARDS

| Service | URL | Purpose |
|---------|-----|---------|
| Prometheus | http://localhost:9090 | Metrics & Alerting |
| Prometheus Alerts | http://localhost:9090/alerts | Active Alerts |
| Grafana | http://localhost:3001 | Dashboards (admin/admin) |
| Alertmanager | http://localhost:9093 | Alert Routing |
| Kibana | http://localhost:5601 | Log Analysis |
| Router | http://localhost:8080/health | API Health |
| NATS Monitor | http://localhost:8222/varz | Message Bus Stats |

---

## STORAGE ARCHITECTURE

### C:\ Drive (Local - Production)
- **Aegentix/** — Production cluster (docker-compose.production.yml)
- **SovereignSystem/** — Autonomous ledger (5055+ items)
- **BlockchainData/** — Node infrastructure (200+ chains)
- **production/** — Kubernetes/Terraform configs
- **policy/** — Trust & governance

### G:\ Drive (Google Drive - Cloud Backup)
- **My Drive/Aegentix/** — Cloud mirror
- **My Drive/FullDeviceBackup/** — Full system backup
- **Documentation/** — 24 .docx architecture files
- **Other computers/** — Cross-device sync

---

## ALERT RULES ACTIVE

| Alert | Condition | Severity |
|-------|-----------|----------|
| AegentixCPUAnomalousSpike | Rate > 0.85 for 20s | CRITICAL |
| AegentixMemoryAllocationLimitExceeded | > 1GB for 45s | WARNING |
| AegentixAgentNodeDropped | Up metric == 0 for 10s | CRITICAL |
| AegentixClusterDegraded | < 4 agents healthy | CRITICAL |
| AegentixMonitoringStackDown | Prometheus/Grafana offline | CRITICAL |

---

## CONTACT & ESCALATION

- **Level 1**: Autonomous response (Healing Agent)
- **Level 2**: Admin dashboard (http://localhost:3001)
- **Level 3**: Manual intervention (ops-guide.ps1)
- **Level 4**: Full system review (SovereignSystem ledger audit)

---

## DOCUMENTATION

- **Architecture**: G:\My Drive\Kimi AEGENTIX AGENTIC FINANCIAL SECURITY STACK v1.0
- **APOSTLE Framework**: G:\My Drive\Kimi APOSTLE™ System Architecture
- **Runbooks**: This file (and ops-guide.ps1)
- **Status**: Always check `.\uoc.ps1 -Operation dashboard`

---

**Last Updated**: $(date)
**Status**: OPERATIONAL
**Version**: 1.0
