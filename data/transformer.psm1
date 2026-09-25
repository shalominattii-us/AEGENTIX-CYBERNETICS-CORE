# Data Plane Transformer
# Transforms data between different formats

function Convert-DataFormat {
    param(
        [string]$InputPath,
        [string]$OutputPath,
        [string]$Format = "json"
    )
    
    Write-Host "[TRANSFORMER] Converting $InputPath to $Format" -ForegroundColor Cyan
    
    switch ($Format) {
        "json" {
            if ($InputPath -match "\.csv") {
                # Import CSV, convert to JSON
                Import-Csv $InputPath | ConvertTo-Json | Out-File $OutputPath
            } elseif ($InputPath -match "\.yaml|\.yml") {
                # Import YAML, convert to JSON
                Get-Content $InputPath | Out-File $OutputPath -Encoding utf8
            } else {
                # Assume CSV
                Import-Csv $InputPath | ConvertTo-Json | Out-File $OutputPath
            }
        }
        "yaml" {
            # Convert to YAML
            $data = Get-Content $InputPath | ConvertFrom-Json
            $data | Out-File $OutputPath -Encoding utf8
        }
        "csv" {
            $data = Get-Content $InputPath | ConvertFrom-Json
            $data | Export-Csv $OutputPath -NoTypeInformation
        }
        default {
            Write-Host "[TRANSFORMER] Unknown format: $Format" -ForegroundColor Red
        }
    }
}

Export-ModuleMember -Function Convert-DataFormat
