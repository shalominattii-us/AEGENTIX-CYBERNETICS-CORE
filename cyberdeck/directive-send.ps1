param(
    [Parameter(Mandatory=True)][string]
)

\ = "aegentix-aegentix-runtime-1"
Write-Host "Sending directive to runtime: \"
docker exec \ sh -c "echo '\' >> /app/directives/inbox.txt"
Write-Host "Directive queued."
