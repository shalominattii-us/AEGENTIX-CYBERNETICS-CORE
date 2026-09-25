# Governance Risk Assessor
# Evaluates risks for system actions

function Assess-Risk {
    param([string]$Action, [string]$Resource, [hashtable]$Context)
    
    $riskScore = 0
    $riskFactors = @()
    
    # Evaluate action risk
    switch ($Action) {
        "delete" { $riskScore += 40; $riskFactors += "Destructive action" }
        "deploy" { $riskScore += 30; $riskFactors += "Production change" }
        "modify" { $riskScore += 20; $riskFactors += "Configuration change" }
        "read"   { $riskScore += 5;  $riskFactors += "Data access" }
        default  { $riskScore += 10 }
    }
    
    # Evaluate resource criticality
    if ($Resource -match "governance|federation|kernel") {
        $riskScore += 30
        $riskFactors += "Critical resource"
    }
    
    if ($Resource -match "blockchain|wallet|treasury") {
        $riskScore += 25
        $riskFactors += "Financial resource"
    }
    
    $result = @{
        action = $Action
        resource = $Resource
        risk_score = [Math]::Min(100, $riskScore)
        factors = $riskFactors
        severity = if ($riskScore -ge 70) { "Critical" } elseif ($riskScore -ge 40) { "High" } elseif ($riskScore -ge 20) { "Medium" } else { "Low" }
        recommended_action = if ($riskScore -ge 70) { "Requires approval" } elseif ($riskScore -ge 40) { "Requires review" } else { "Auto-approve" }
        assessed_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    return $result
}

Export-ModuleMember -Function Assess-Risk
