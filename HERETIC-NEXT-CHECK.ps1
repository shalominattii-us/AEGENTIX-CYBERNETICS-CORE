$ErrorActionPreference = "SilentlyContinue"

$Report = "C:\Aegentix\HERETIC-NEXT-CHECK.txt"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " AEGENTIX — HERETIC NEXT CHECK" -ForegroundColor Cyan
Write-Host " READ-ONLY / NO DOWNLOADS / NO CHANGES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Lines = [System.Collections.Generic.List[string]]::new()

function Add-Line {
    param([string]$Text = "")
    $Lines.Add($Text)
    Write-Host $Text
}

function Add-Section {
    param([string]$Text)
    Add-Line ""
    Add-Line "------------------------------------------------------------"
    Add-Line $Text
    Add-Line "------------------------------------------------------------"
}

# ============================================================
# SYSTEM
# ============================================================

Add-Section "1. SYSTEM / HARDWARE"

$Computer = Get-CimInstance Win32_ComputerSystem
$OS = Get-CimInstance Win32_OperatingSystem
$CPU = Get-CimInstance Win32_Processor | Select-Object -First 1
$GPU = Get-CimInstance Win32_VideoController

Add-Line ("Computer        : " + $Computer.Manufacturer + " " + $Computer.Model)
Add-Line ("OS              : " + $OS.Caption)
Add-Line ("OS Build        : " + $OS.BuildNumber)
Add-Line ("CPU             : " + $CPU.Name)
Add-Line ("Logical CPUs    : " + $CPU.NumberOfLogicalProcessors)
Add-Line ("RAM             : " + [math]::Round($Computer.TotalPhysicalMemory / 1GB, 2) + " GB")

foreach ($G in $GPU) {
    Add-Line ""
    Add-Line ("GPU             : " + $G.Name)
    if ($G.AdapterRAM) {
        Add-Line ("GPU RAM         : " + [math]::Round($G.AdapterRAM / 1GB, 2) + " GB")
    }
    Add-Line ("Driver          : " + $G.DriverVersion)
}

# ============================================================
# PYTHON
# ============================================================

Add-Section "2. PYTHON"

$PythonCandidates = @(
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python313\python.exe",
    "C:\Program Files\Python314\python.exe"
)

foreach ($Py in $PythonCandidates) {
    if (Test-Path -LiteralPath $Py) {
        $V = & $Py --version 2>&1
        Add-Line ("FOUND           : " + $Py)
        Add-Line ("VERSION         : " + ($V -join " "))
    }
}

$PyWhere = Get-Command python.exe -ErrorAction SilentlyContinue
if ($PyWhere) {
    Add-Line ("PATH PYTHON     : " + $PyWhere.Source)
    Add-Line ("PATH VERSION    : " + ((& python.exe --version 2>&1) -join " "))
}

# ============================================================
# HERETIC
# ============================================================

Add-Section "3. HERETIC"

$HereticCmd = Get-Command heretic.exe -ErrorAction SilentlyContinue

if ($HereticCmd) {
    Add-Line ("HERETIC EXE     : " + $HereticCmd.Source)
    $HV = & heretic.exe --version 2>&1
    Add-Line ("HERETIC VERSION : " + ($HV -join " "))

    Add-Line ""
    Add-Line "HERETIC HELP:"
    $Help = & heretic.exe --help 2>&1
    foreach ($H in $Help) {
        if ($H -match "--model|--quantization|--device-map|--max-memory|--batch-size|--dtypes") {
            Add-Line $H
        }
    }
}
else {
    Add-Line "HERETIC EXE     : NOT FOUND"
}

# ============================================================
# PYTORCH
# ============================================================

Add-Section "4. PYTORCH / CUDA"

$PyTorchChecked = $false

foreach ($Py in $PythonCandidates) {
    if (-not (Test-Path -LiteralPath $Py)) { continue }

    $TorchInfo = & $Py -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.device_count()); [print(torch.cuda.get_device_name(i)) for i in range(torch.cuda.device_count())]" 2>&1

    if ($LASTEXITCODE -eq 0 -and $TorchInfo) {
        Add-Line ("PYTHON          : " + $Py)
        foreach ($T in $TorchInfo) {
            Add-Line ("TORCH           : " + $T)
        }
        $PyTorchChecked = $true
        break
    }
}

if (-not $PyTorchChecked) {
    Add-Line "PyTorch import   : NOT AVAILABLE IN CHECKED PYTHONS"
}

# ============================================================
# EXISTING GGUF MODELS
# ============================================================

Add-Section "5. EXISTING LARGE GGUF MODELS"

$ModelRoots = @(
    "$env:USERPROFILE\.lmstudio\models",
    "$env:USERPROFILE\.cache\huggingface",
    "C:\Aegentix",
    "G:\"
)

$GGUF = [System.Collections.Generic.List[object]]::new()
$Seen = @{}

foreach ($Root in $ModelRoots) {
    if (-not (Test-Path -LiteralPath $Root)) { continue }

    Write-Host ("Scanning models: " + $Root) -ForegroundColor DarkGray

    Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "*.gguf" -ErrorAction SilentlyContinue |
        ForEach-Object {
            $Key = $_.FullName.ToLowerInvariant()

            if (-not $Seen.ContainsKey($Key)) {
                $Seen[$Key] = $true

                if ($_.Length -ge 100MB) {
                    $GGUF.Add([PSCustomObject]@{
                        GB = [math]::Round($_.Length / 1GB, 3)
                        Size = $_.Length
                        Path = $_.FullName
                    })
                }
            }
        }
}

$GGUF = $GGUF | Sort-Object Size -Descending

if ($GGUF.Count -eq 0) {
    Add-Line "No large GGUF files found."
}
else {
    foreach ($M in $GGUF) {
        Add-Line ("{0,8} GB  {1}" -f $M.GB, $M.Path)
    }
}

# ============================================================
# TRANSFORMERS DIRECTORIES
# ============================================================

Add-Section "6. TRANSFORMERS MODEL DIRECTORIES"

$Candidates = [System.Collections.Generic.List[object]]::new()
$SeenConfigs = @{}

foreach ($Root in @(
    "$env:USERPROFILE\.cache\huggingface\hub",
    "$env:USERPROFILE",
    "C:\Aegentix"
)) {
    if (-not (Test-Path -LiteralPath $Root)) { continue }

    Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "config.json" -ErrorAction SilentlyContinue |
        ForEach-Object {

            $ConfigPath = $_.FullName
            if ($SeenConfigs.ContainsKey($ConfigPath.ToLowerInvariant())) { return }
            $SeenConfigs[$ConfigPath.ToLowerInvariant()] = $true

            $Dir = $_.Directory.FullName

            $Weights = @(
                Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.Extension -in @(
                            ".safetensors",
                            ".bin",
                            ".pt",
                            ".pth"
                        ) -and $_.Length -gt 1MB
                    }
            )

            if ($Weights.Count -gt 0) {
                try {
                    $Cfg = Get-Content -LiteralPath $ConfigPath -Raw |
                        ConvertFrom-Json

                    $Candidates.Add([PSCustomObject]@{
                        ModelType = $Cfg.model_type
                        Architecture = ($Cfg.architectures -join ", ")
                        WeightGB = [math]::Round(
                            (($Weights | Measure-Object Length -Sum).Sum / 1GB), 3
                        )
                        Files = $Weights.Count
                        Path = $Dir
                    })
                }
                catch {}
            }
        }
}

$Candidates = $Candidates |
    Sort-Object Path -Unique |
    Sort-Object WeightGB -Descending

if ($Candidates.Count -eq 0) {
    Add-Line "NO COMPLETE TRANSFORMERS MODELS FOUND."
}
else {
    foreach ($C in $Candidates) {
        Add-Line ""
        Add-Line ("MODEL TYPE      : " + $C.ModelType)
        Add-Line ("ARCHITECTURE    : " + $C.Architecture)
        Add-Line ("WEIGHTS         : " + $C.Files + " files / " + $C.WeightGB + " GB")
        Add-Line ("PATH            : " + $C.Path)
    }
}

# ============================================================
# QWEN3.5 HOLLOW SNAPSHOT
# ============================================================

Add-Section "7. QWEN3.5-4B SNAPSHOT CHECK"

$Qwen35 = Get-ChildItem `
    -LiteralPath "$env:USERPROFILE\.cache\huggingface\hub\models--Qwen--Qwen3.5-4B\snapshots" `
    -Directory `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($Qwen35) {
    $Files = @(Get-ChildItem -LiteralPath $Qwen35.FullName -Recurse -File -ErrorAction SilentlyContinue)
    $Bytes = ($Files | Measure-Object Length -Sum).Sum

    Add-Line ("SNAPSHOT        : " + $Qwen35.FullName)
    Add-Line ("FILES           : " + $Files.Count)
    Add-Line ("TOTAL BYTES     : " + $Bytes)

    if ($Bytes -eq 0) {
        Add-Line "STATUS          : HOLLOW / UNUSABLE" 
    }
    else {
        Add-Line "STATUS          : NONZERO DATA PRESENT"
    }
}
else {
    Add-Line "Qwen3.5-4B snapshot not found."
}

# ============================================================
# DISK SPACE
# ============================================================

Add-Section "8. DISK SPACE"

foreach ($Drive in @("C","G")) {
    $D = Get-PSDrive -Name $Drive -ErrorAction SilentlyContinue

    if ($D) {
        Add-Line ("{0}: FREE {1} GB / USED {2} GB" -f `
            $Drive,
            [math]::Round($D.Free / 1GB, 2),
            [math]::Round($D.Used / 1GB, 2))
    }
}

# ============================================================
# DECISION
# ============================================================

Add-Section "9. HERETIC DECISION"

if ($Candidates.Count -gt 0) {

    Add-Line "A complete Transformers model already exists."
    Add-Line "DO NOT DOWNLOAD ANOTHER MODEL YET."

    $Smallest = $Candidates |
        Sort-Object WeightGB |
        Select-Object -First 1

    Add-Line ""
    Add-Line ("SMALLEST LOCAL TRANSFORMERS MODEL: " + $Smallest.WeightGB + " GB")
    Add-Line ("PATH: " + $Smallest.Path)

}
else {

    Add-Line "NO COMPLETE LOCAL TRANSFORMERS MODEL IS AVAILABLE."
    Add-Line ""
    Add-Line "Existing large GGUF models can be used by LM Studio/llama.cpp,"
    Add-Line "but they are NOT a direct Heretic input target."
    Add-Line ""
    Add-Line "NEXT TARGET SHOULD BE A SMALL TRANSFORMERS MODEL."
    Add-Line "Do NOT start a 27B/50GB download on this machine yet."
    Add-Line ""
    Add-Line "Candidate class to investigate:"
    Add-Line "  Qwen3 4B / similar 4B Transformers model"
    Add-Line ""
    Add-Line "Heretic supports 4-bit loading, so a small Transformers model"
    Add-Line "is the sensible hardware-validation target before attempting"
    Add-Line "larger models."
}

# ============================================================
# SAVE
# ============================================================

$Lines |
    Set-Content -LiteralPath $Report -Encoding UTF8

Add-Line ""
Add-Line "============================================================"
Add-Line ("REPORT: " + $Report)
Add-Line "NO FILES CHANGED"
Add-Line "NO MODELS DOWNLOADED"
Add-Line "============================================================"
