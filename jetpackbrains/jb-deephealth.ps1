function JB-DeepHealth { param([string]$c) $h = docker inspect --format "{{.State.Health.Status}}" $c 2>$null; if ($h -eq "unhealthy") { return $false } return $true }
