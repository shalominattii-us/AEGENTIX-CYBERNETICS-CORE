param(
    [Parameter(Mandatory=True)][string]
)

\ = @(
    "aegentix-aegentix-runtime-1",
    "aegentix-aegentix-mcp-http-1",
    "aegentix-aegentix-mcp-system-1",
    "aegentix-aegentix-mcp-fs-1",
    "aegentix-aegentix-gaia-1",
    "aegentix-aegentix-directive-1",
    "aegentix-aegentix-hud-1"
)

foreach (\ in \) {
    Write-Host "Broadcasting to \"
    docker exec \ sh -c "echo '\' >> /app/directives/inbox.txt"
}
Write-Host "Broadcast complete."
