\Continue = "Continue"
\default = "default"

Write-Host "==> Checking Kubernetes Connection..." -ForegroundColor Cyan
\ = kubectl cluster-info 2>&1
if (\1 -ne 0) {
    Write-Host "[!] No active Kubernetes cluster detected on localhost." -ForegroundColor Red
    Write-Host "[i] Switching evaluation focus to local Docker Compose stack..." -ForegroundColor Yellow
    docker compose -f docker-compose.autonomous.yml ps
    exit 0
}

Write-Host "
[✓] Kubernetes control plane active. Checking healing-agent permissions..." -ForegroundColor Green
\ = (kubectl auth can-i delete pods --as=system:serviceaccount:\default:healing-agent 2>&1).Trim()

if (\ -eq "yes") {
    Write-Host "RESULT: Healing Agent Superpowers are fully operational!" -ForegroundColor Green
} else {
    Write-Host "RESULT: RBAC checks failed or pending manifest application." -ForegroundColor Red
}
