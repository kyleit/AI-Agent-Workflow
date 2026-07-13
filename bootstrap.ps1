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
    Write-Host "  memory       Manage project memory (bootstrap, update, search)"
    Write-Host "  blueprint    Register or approve design blueprints"
    Write-Host "  registry     Manage centralized global project registry"
    Write-Host "  provider     Manage external knowledge providers (sync, list, config)"
    Write-Host "  sync         Sync project memory/documentation to external providers (e.g. Obsidian)"
    Write-Host "  bootstrap    Run framework environment bootstrap installer"
    Write-Host "  init         Initialize a new project workspace (collect specification, generate configs)"
    Write-Host "  update-source Update the centralized framework source repository safely via Git"
    Write-Host "  test         Execute test validate, smoke, or affected tests"
    Write-Host "  workflow     Submit, inspect, track, or manage active SDLC workflows"
    Write-Host "  session      Recover, inspect, lock, or update active workspace sessions"
    Write-Host "  mcp          Automatically install, uninstall, validate, or check status of MCP Tool servers"
    Write-Host "  help         Show this help message"
}

if ([string]::IsNullOrEmpty(`$Command)) {
    Show-Help
    exit 1
}

switch (`$Command) {
    "bootstrap" {
        & (Join-Path `$FrameworkRoot "bootstrap.ps1") @args
    }
    "init" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") init @args
    }
    "update-source" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") update-source @args
    }
    "test" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") test @args
    }
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
    "memory" {
        python (Join-Path `$FrameworkRoot "runtime/scripts/project_memory/cli.py") @args
    }
    "blueprint" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") blueprint @args
    }
    "registry" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") registry @args
    }
    "provider" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") provider @args
    }
    "sync" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") provider sync @args
    }
    "help" {
        Show-Help
    }

    default {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") `$Command @args
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
