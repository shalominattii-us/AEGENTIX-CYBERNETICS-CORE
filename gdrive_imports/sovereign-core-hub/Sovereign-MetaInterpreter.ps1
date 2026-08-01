param(
    [ValidateSet("describe","engines","run","timeline")]
    [string]$Action = "describe",
    [string]$Engine,
    [string]$Mode = "full"
)

$meta = Get-Content "C:\Sovereign\Sovereign-MetaArtifact.sovmeta" -Raw

function Extract {
    param($key)
    ($meta -split "`n" | Where-Object { $_ -match "^$key:" }) -replace "^$key:\s*","" -replace '"',''
}

function ExtractList {
    param($key)
    $start = $meta.IndexOf("$key:")
    if ($start -lt 0) { return @() }
    $open = $meta.IndexOf("[",$start)
    $close = $meta.IndexOf("]",$open)
    $block = $meta.Substring($open+1,$close-$open-1)
    return $block -split "`n" | ForEach-Object { $_.Trim().Trim('"').Trim(',') } | Where-Object { $_ }
}

$stack = Extract "stack"
$core  = Extract "core"
$man   = Extract "manifest"
$engs  = ExtractList "engines"

if ($Action -eq "describe") {
    Write-Host "Stack: $stack"
    Write-Host "Core: $core"
    Write-Host "Manifest: $man"
    Write-Host "Engines:"
    $engs | ForEach-Object { Write-Host " - $_" }
    exit
}

if ($Action -eq "engines") {
    $engs | ForEach-Object { Write-Host $_ }
    exit
}

if ($Action -eq "run") {
    & "C:\Sovereign\Sovereign-LRV.ps1" -Action run -Engine $Engine -Mode $Mode
    exit
}

if ($Action -eq "timeline") {
    $start = $meta.IndexOf("chronicle_last_2_hours")
    $open = $meta.IndexOf("{",$start)
    $close = $meta.IndexOf("}",$open)
    $block = $meta.Substring($open+1,$close-$open-1)
    $block -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    exit
}
