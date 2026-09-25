param()

\ = "aegentix-aegentix-runtime-1"
Write-Host "Pinging runtime..."
docker exec \ sh -c "echo 'ping' >> /app/directives/inbox.txt"
Start-Sleep -Seconds 1
docker exec \ sh -c "tail -n 5 /app/directives/outbox.txt"
