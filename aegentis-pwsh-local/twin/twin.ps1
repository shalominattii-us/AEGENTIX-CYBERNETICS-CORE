Add-Type -AssemblyName System.Net.WebSockets
Add-Type -AssemblyName System.Runtime

\ = "ws://aegentis-router:8080/api/trpc"
\ = New-Object System.Net.WebSockets.ClientWebSocket

Write-Host "Twin connecting to \"
\.ConnectAsync([Uri]\, [System.Threading.CancellationToken]::None).Wait()

\ = [System.Text.Encoding]::UTF8.GetBytes("twin-online")
\.SendAsync(
    (New-Object System.ArraySegment[byte] \),
    [System.Net.WebSockets.WebSocketMessageType]::Text,
    \True,
    [System.Threading.CancellationToken]::None
).Wait()

\ = New-Object System.ArraySegment[byte] (1024)
\ = \.ReceiveAsync(\, [System.Threading.CancellationToken]::None).Result

\ = [System.Text.Encoding]::UTF8.GetString(\.Array, 0, \.Count)
Write-Host "Router replied: \"

\.Dispose()
