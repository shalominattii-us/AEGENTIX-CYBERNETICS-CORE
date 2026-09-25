# AEGENTIX UOC - COMMAND REFERENCE

## Operations Commands

### View Dashboard
```powershell
.\uoc.ps1 -Operation dashboard
```

### Check Status
```powershell
.\uoc.ps1 -Operation status
```

### Agent Health
```powershell
.\uoc.ps1 -Operation health
.\uoc.ps1 -Operation agents
```

### Control Stack

**Start:**
```powershell
.\uoc.ps1 -Operation start
```

**Stop:**
```powershell
.\uoc.ps1 -Operation stop
```

**Restart:**
```powershell
.\uoc.ps1 -Operation restart
```

### View Logs
```powershell
.\uoc.ps1 -Operation logs
```

### Infrastructure Status
```powershell
.\uoc.ps1 -Operation blockchain
.\uoc.ps1 -Operation sovereign
.\uoc.ps1 -Operation backup
```

---

## Direct Docker Commands

### Check All Services
```powershell
docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
```

### View Agent Logs
```powershell
docker logs aegentix-agent-monitoring --tail 20
docker logs aegentix-agent-incident-response --tail 20
docker logs aegentix-agent-healing --tail 20
docker logs aegentix-agent-autoscaling --tail 20
docker logs aegentix-agent-deployment --tail 20
```

### View Threat Detection
```powershell
docker logs aegentix-telemetry-engine --tail 50
```

### Real-time Monitoring
```powershell
docker logs -f aegentix-agent-monitoring
```

---

## Web Dashboards

| Dashboard | URL |
|-----------|-----|
| Prometheus Alerts | http://localhost:9090/alerts |
| Prometheus Metrics | http://localhost:9090/graph |
| Grafana | http://localhost:3001 |
| Alertmanager | http://localhost:9093 |
| Kibana | http://localhost:5601 |
| Router Health | http://localhost:8080/health |
| NATS Stats | http://localhost:8222/varz |

---

## Common Troubleshooting

### Restart Single Service
```powershell
docker compose -f C:\Aegentix\docker-compose.production.yml restart aegentix-telemetry-engine
```

### View Recent Alerts
```powershell
curl -s http://localhost:9093/api/v1/alerts | ConvertFrom-Json
```

### Check Prometheus Rules
```powershell
curl -s http://localhost:9090/api/v1/rules | ConvertFrom-Json
```

### Export Metrics
```powershell
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=up" -OutFile "metrics.json"
```

### Blockchain Status
```powershell
Get-Content C:\BlockchainData\nodes.json | ConvertFrom-Json | Select-Object -First 10
```

### Ledger Status
```powershell
Get-ChildItem C:\SovereignSystem\ledger -Recurse | Measure-Object -Property Length -Sum
```

---

## Emergency Commands

### Stop Everything
```powershell
cd C:\Aegentix
docker compose -f docker-compose.production.yml down
```

### Start Everything
```powershell
cd C:\Aegentix
docker compose -f docker-compose.production.yml up -d --pull always
```

### Full System Health Check
```powershell
.\uoc.ps1 -Operation dashboard
```

### View All Containers
```powershell
docker ps -a
```

### Check Docker System
```powershell
docker system df
docker system info
```
