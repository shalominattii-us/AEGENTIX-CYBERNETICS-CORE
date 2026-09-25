param()

\ = "aegentix-aegentix-runtime-1"
Write-Host "Streaming runtime directive output..."
docker exec -it \ sh -c "tail -f /app/directives/outbox.txt"
