# ==============================================================================
# AI Skill Framework Global Bootstrap Installer (Windows PowerShell)
# Installs the global 'aiwf' command-line interface.
# ==============================================================================

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Error "[ERROR] $msg" }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# 1. Detect source framework location (where bootstrap.ps1 is located)
$FrameworkDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($FrameworkDir)) { $FrameworkDir = Get-Location }
Log-Info "Framework source located at: $FrameworkDir"

# 2. Determine installation directory for global binary wrapper
$InstallDir = Join-Path $env:LOCALAPPDATA "aiwf"
$BinDir = Join-Path $InstallDir "bin"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

# 3. Create the global 'aiwf.ps1' executable CLI wrapper
$CliPath = Join-Path $BinDir "aiwf.ps1"
Log-Info "Creating CLI wrapper at: $CliPath"

$CliContent = @"
# ==============================================================================
# AI Skill Framework Global CLI Wrapper (aiwf.ps1)
# ==============================================================================
param(
    [string]`$Command
)

# Dynamic framework directory replaced during bootstrap
`$FrameworkRoot = "$FrameworkDir"

function Show-Help {
    Write-Host "AI Skill Framework CLI"
    Write-Host "Usage: aiwf <command> [options]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  install      Install framework skills into the current Git project"
    Write-Host "  update       Synchronize installed skills with latest repo version"
    Write-Host "  uninstall    Safely remove framework skills from the current project"
    Write-Host "  doctor       Perform diagnostic verification of framework state"
    Write-Host "  version      Report current CLI and repository versions"
    Write-Host "  help         Show this help message"
}

if ([string]::IsNullOrEmpty(`$Command)) {
    Show-Help
    exit 1
}

switch (`$Command) {
    "install" {
        & (Join-Path `$FrameworkRoot "install.ps1") @args
    }
    "update" {
        & (Join-Path `$FrameworkRoot "update.ps1") @args
    }
    "uninstall" {
        & (Join-Path `$FrameworkRoot "uninstall.ps1") @args
    }
    "doctor" {
        & (Join-Path `$FrameworkRoot "doctor.ps1") @args
    }
    "version" {
        & (Join-Path `$FrameworkRoot "version.ps1") @args
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: `$Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
"@

Set-Content -Path $CliPath -Value $CliContent -Force | Out-Null

# 4. PATH Configuration (User Environment Variables)
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notmatch [regex]::Escape($BinDir)) {
    Log-Info "Adding $BinDir to PATH User Environment Variable"
    $NewPath = $UserPath
    if (-not $NewPath.EndsWith(";")) { $NewPath += ";" }
    $NewPath += "$BinDir;"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
}
else {
    Log-Info "PATH configuration already exists in User environment variables."
}

# Update active process session PATH
$env:Path = "$env:Path;$BinDir"

# 5. Success Summary and verification instructions
Log-Success "AI Skill Framework CLI wrapper 'aiwf' has been created!"
Write-Host "--------------------------------------------------"
Write-Host "Global Bootstrap Summary:"
Write-Host "  CLI Location:      $CliPath"
Write-Host "  Framework Source:  $FrameworkDir"
Write-Host "--------------------------------------------------"
Log-Info "The CLI has been registered. You may need to restart your terminal for PATH changes to take full effect."
Log-Info "To verify, restart your terminal and run:  aiwf version"
Log-Info "Or diagnostic test: aiwf doctor"
