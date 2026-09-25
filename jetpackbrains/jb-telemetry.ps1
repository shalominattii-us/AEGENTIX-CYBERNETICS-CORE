function JB-Telemetry { $data=@{uptime=(Get-Date)-$global:daemonStart; sovereignLast=$global:sovereignLast; jbLast=$global:jbLast}; return $data }
