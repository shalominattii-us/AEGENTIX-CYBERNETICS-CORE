$out = 'C:\Aegentix\logs\lem-test.log'
"START $(Get-Date -Format o)" | Set-Content $out
foreach ($m in @('Qwen3-0.6B-GGUF','Qwen3-0.6B-GGUF:latest')) {
  $sw=[Diagnostics.Stopwatch]::StartNew()
  try {
    $body=@{model=$m;messages=@(@{role='user';content='Say OK'});max_tokens=8}|ConvertTo-Json -Compress
    $r=Invoke-RestMethod -Uri 'http://localhost:11434/api/v1/chat/completions' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 240
    "$m -> OK in $([int]$sw.Elapsed.TotalSeconds)s : $($r.choices[0].message.content)" | Add-Content $out
  } catch { "$m -> FAIL in $([int]$sw.Elapsed.TotalSeconds)s : $($_.Exception.Message)" | Add-Content $out }
}
"END" | Add-Content $out
