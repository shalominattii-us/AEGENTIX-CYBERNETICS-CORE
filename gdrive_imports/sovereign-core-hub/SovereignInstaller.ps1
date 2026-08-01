# ============================================================
# SOVEREIGN ONE-SHOT LOCAL INSTALLER
# Single file. No payload. No repo. Full bootstrap.
# Target root: C:\Sovereign
# ============================================================

$ErrorActionPreference = "Stop"

# ------------------ CONFIG ------------------
$Root        = "C:\Sovereign"
$PortalPath  = Join-Path $Root "SovereignPortal"
$RuntimesDir = Join-Path $Root "runtimes"
$HyperxDir   = Join-Path $RuntimesDir "hyperx_fabric_vnext"
$ConfigDir   = Join-Path $Root "config"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Ω SOVEREIGN ONE-SHOT INSTALLER    " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# ------------------ HELPERS ------------------
function Ensure-Folder {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Check-Dep {
    param(
        [string]$cmd,
        [string]$hint
    )

    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[X] Missing dependency: $cmd" -ForegroundColor Red
        Write-Host "    Install from: $hint" -ForegroundColor Yellow
        throw "Missing dependency: $cmd"
    } else {
        Write-Host "[OK] $cmd detected." -ForegroundColor Green
    }
}

# ------------------ STEP 1: FOLDERS ------------------
Write-Host "[Ω] Creating Sovereign directory structure..." -ForegroundColor Cyan

Ensure-Folder $Root
Ensure-Folder $RuntimesDir
Ensure-Folder $HyperxDir
Ensure-Folder (Join-Path $Root "models")
Ensure-Folder (Join-Path $Root "federation")
Ensure-Folder (Join-Path $Root "memory")
Ensure-Folder (Join-Path $Root "logs")
Ensure-Folder $ConfigDir

Write-Host "[OK] Folder structure ready." -ForegroundColor Green

# ------------------ STEP 2: DEPENDENCIES ------------------
Write-Host "[Ω] Checking dependencies..." -ForegroundColor Cyan

Check-Dep "dotnet" "https://dotnet.microsoft.com/download"
Check-Dep "cmake"  "https://cmake.org/download"
Check-Dep "git"    "https://git-scm.com/downloads"
Check-Dep "ollama" "https://ollama.com/download"

Write-Host "[Ω] All required dependencies present." -ForegroundColor Green

# ------------------ STEP 3: OLLAMA MODELS ------------------
Write-Host "[Ω] Verifying Ollama models..." -ForegroundColor Cyan

try {
    $models = ollama list
} catch {
    Write-Host "[X] Failed to query Ollama. Make sure 'ollama serve' can run." -ForegroundColor Red
    throw
}

if ($models -notmatch "llama3") { ollama pull llama3 }
if ($models -notmatch "qwen2")  { ollama pull qwen2 }
if ($models -notmatch "gemma")  { ollama pull gemma }

Write-Host "[OK] Ollama models ready." -ForegroundColor Green

# ------------------ STEP 4: SOVEREIGNPORTAL (WINUI 3) ------------------
Write-Host "[Ω] Ensuring SovereignPortal exists..." -ForegroundColor Cyan

if (-not (Test-Path $PortalPath)) {
    Write-Host "[…] Creating new WinUI SovereignPortal project..." -ForegroundColor Yellow
    Ensure-Folder $PortalPath

    Push-Location $Root
    dotnet new winui -n SovereignPortal -o SovereignPortal
    Pop-Location
} else {
    Write-Host "[OK] SovereignPortal folder already exists." -ForegroundColor Green
}

# Replace MainWindow.xaml with Sovereign shell
$MainWindowXaml = Join-Path $PortalPath "MainWindow.xaml"
@"
<Window
    x:Class="SovereignPortal.MainWindow"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:local="using:SovereignPortal"
    Title="Sovereign Portal"
    Width="1280"
    Height="800">

    <Grid>
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="240"/>
            <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>

        <StackPanel Background="#111111" Padding="20">
            <TextBlock Text="Ω Sovereign Portal" 
                       Foreground="White" 
                       FontSize="20"
                       Margin="0 0 0 20"/>

            <Button Content="Dialogue"
                    Tag="DialogueView"
                    Margin="0 5"/>

            <Button Content="Commander Console"
                    Tag="CommanderConsoleView"
                    Margin="0 5"/>

            <Button Content="Federation Mesh"
                    Tag="FederationView"
                    Margin="0 5"/>

            <Button Content="Memory Ledger"
                    Tag="MemoryLedgerView"
                    Margin="0 5"/>
        </StackPanel>

        <Frame x:Name="MainFrame"
               Grid.Column="1"
               Background="#0D0D0D"/>
    </Grid>
</Window>
"@ | Set-Content $MainWindowXaml -Encoding UTF8

# Create Views folder + basic views
$ViewsDir = Join-Path $PortalPath "Views"
Ensure-Folder $ViewsDir

@"
<Page
    x:Class="SovereignPortal.Views.DialogueView"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <Grid Background="#0D0D0D">
        <Grid.RowDefinitions>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <ScrollViewer Grid.Row="0">
            <StackPanel x:Name="MessageStack" Margin="20"/>
        </ScrollViewer>

        <StackPanel Grid.Row="1" Orientation="Horizontal" Padding="20">
            <TextBox x:Name="InputBox"
                     Width="900"
                     PlaceholderText="Enter command..."
                     Margin="0 0 20 0"/>

            <Button Content="Send"
                    Width="120"
                    x:Name="SendButton"/>
        </StackPanel>
    </Grid>
</Page>
"@ | Set-Content (Join-Path $ViewsDir "DialogueView.xaml") -Encoding UTF8

@"
<Page
    x:Class="SovereignPortal.Views.CommanderConsoleView"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <Grid Background="#000000">
        <Grid.RowDefinitions>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <ScrollViewer Grid.Row="0">
            <TextBlock x:Name="ConsoleOutput"
                       FontFamily="Consolas"
                       FontSize="14"
                       Foreground="#00FF00"
                       Margin="20"/>
        </ScrollViewer>

        <StackPanel Grid.Row="1" Orientation="Horizontal" Padding="20">
            <TextBox x:Name="ConsoleInput"
                     Width="900"
                     FontFamily="Consolas"
                     PlaceholderText="hyperx>"/>

            <Button Content="Execute"
                    Width="120"
                    x:Name="ExecuteButton"
                    Margin="20 0 0 0"/>
        </StackPanel>
    </Grid>
</Page>
"@ | Set-Content (Join-Path $ViewsDir "CommanderConsoleView.xaml") -Encoding UTF8

@"
<Page
    x:Class="SovereignPortal.Views.FederationView"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <Grid Background="#0A0A0A">
        <Canvas x:Name="MeshCanvas"/>
    </Grid>
</Page>
"@ | Set-Content (Join-Path $ViewsDir "FederationView.xaml") -Encoding UTF8

@"
<Page
    x:Class="SovereignPortal.Views.MemoryLedgerView"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <Grid Background="#0D0D0D">
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="300"/>
            <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>

        <ListView x:Name="LedgerList"
                  Grid.Column="0"
                  Background="#111111"
                  Foreground="White"
                  Margin="10"/>

        <ScrollViewer Grid.Column="1" Margin="10">
            <StackPanel x:Name="LedgerDetails"/>
        </ScrollViewer>
    </Grid>
</Page>
"@ | Set-Content (Join-Path $ViewsDir "MemoryLedgerView.xaml") -Encoding UTF8

# MainWindow.xaml.cs minimal wiring
$MainWindowCs = Join-Path $PortalPath "MainWindow.xaml.cs"
@"
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using SovereignPortal.Views;

namespace SovereignPortal
{
    public sealed partial class MainWindow : Window
    {
        public MainWindow()
        {
            this.InitializeComponent();
            MainFrame.Navigate(typeof(DialogueView));
        }
    }
}
"@ | Set-Content $MainWindowCs -Encoding UTF8

Write-Host "[Ω] Building SovereignPortal..." -ForegroundColor Cyan
Push-Location $PortalPath
dotnet restore
dotnet build
Pop-Location
Write-Host "[OK] SovereignPortal built." -ForegroundColor Green

# ------------------ STEP 5: MINIMAL RUNTIME + REGISTRY ------------------
Write-Host "[Ω] Creating minimal runtime registry..." -ForegroundColor Cyan

$RuntimeRegistry = Join-Path $ConfigDir "runtime_registry.json"
@"
{
  "default_runtime": "hyperx_fabric_vnext",
  "runtimes": [
    {
      "id": "hyperx_fabric_vnext",
      "path": ".\\\\runtimes\\\\hyperx_fabric_vnext\\\\hyperx_fabric.exe",
      "args": []
    }
  ]
}
"@ | Set-Content $RuntimeRegistry -Encoding UTF8

Write-Host "[OK] Runtime registry created." -ForegroundColor Green

# ------------------ FINAL STATUS ------------------
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Ω SOVEREIGN SYSTEM INSTALLED Ω    " -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Root:    $Root"
Write-Host "Portal:  $PortalPath"
Write-Host ""
Write-Host "To launch manually:" -ForegroundColor Yellow
Write-Host "  1) Start Ollama server (if not already):"
Write-Host "       ollama serve"
Write-Host "  2) Run SovereignPortal:"
Write-Host "       cd `"$PortalPath`""
Write-Host "       dotnet run"
Write-Host ""
