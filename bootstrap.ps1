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
    Write-Host "Core Bootstrap Commands:"
    Write-Host "  install      Install framework skills into the current Git project"
    Write-Host "  update       Synchronize installed skills with latest repo version"
    Write-Host "  --update     Update the global framework source from GitHub"
    Write-Host "  uninstall    Safely remove framework skills from the current project"
    Write-Host "  doctor       Perform diagnostic verification of framework state"
    Write-Host "  version      Report current CLI and repository versions"
    Write-Host "  bootstrap    Run framework environment bootstrap installer"
    Write-Host ""
    Write-Host "--------------------------------------------------------"
    
    `$oldPythonPath = `$env:PYTHONPATH
    `$env:PYTHONPATH = Join-Path `$FrameworkRoot "skills/workflow-runtime"
    python -m workflow_runtime --help
    `$env:PYTHONPATH = `$oldPythonPath
}

if (-not `$Command) {
    Show-Help
    exit 1
}

function Show-CoreCommandHelp([string]`$Name) {
    switch (`$Name) {
        "install" {
            Write-Host "Usage: aiwf install [-Force] [-Permission <mode>]"
            Write-Host "Install framework skills into the current Git project."
        }
        "update" {
            Write-Host "Usage: aiwf update [options]"
            Write-Host "Synchronize installed framework assets with the source package."
        }
        "uninstall" {
            Write-Host "Usage: aiwf uninstall [options]"
            Write-Host "Safely remove framework-managed assets from the current project."
        }
        "doctor" {
            Write-Host "Usage: aiwf doctor [options]"
            Write-Host "Run framework diagnostic checks."
        }
        "version" {
            Write-Host "Usage: aiwf version"
            Write-Host "Show AIWF version information."
        }
        "bootstrap" {
            Write-Host "Usage: aiwf bootstrap"
            Write-Host "Install or refresh the global aiwf CLI wrapper."
        }
        default { Show-Help }
    }
}

if (`$args -contains "--help" -or `$args -contains "-h" -or `$args -contains "/?") {
    switch (`$Command) {
        "bootstrap" { Show-CoreCommandHelp `$Command; exit 0 }
        "install" { Show-CoreCommandHelp `$Command; exit 0 }
        "update" { Show-CoreCommandHelp `$Command; exit 0 }
        "uninstall" { Show-CoreCommandHelp `$Command; exit 0 }
        "doctor" { Show-CoreCommandHelp `$Command; exit 0 }
        "version" { Show-CoreCommandHelp `$Command; exit 0 }
    }
}

if (`$Command -eq "--update") {
    `$oldPythonPath = `$env:PYTHONPATH
    `$oldFrameworkRoot = `$env:AIWF_FRAMEWORK_ROOT
    `$env:AIWF_FRAMEWORK_ROOT = `$FrameworkRoot
    `$env:PYTHONPATH = Join-Path `$FrameworkRoot "skills/workflow-runtime"
    python -m workflow_runtime self-upgrade @args
    `$exitCode = `$LASTEXITCODE
    `$env:PYTHONPATH = `$oldPythonPath
    if (`$null -eq `$oldFrameworkRoot) { Remove-Item Env:AIWF_FRAMEWORK_ROOT -ErrorAction SilentlyContinue }
    else { `$env:AIWF_FRAMEWORK_ROOT = `$oldFrameworkRoot }
    exit `$exitCode
}

switch (`$Command) {
    "bootstrap" {
        & (Join-Path `$FrameworkRoot "bootstrap.ps1") @args
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
    "help" {
        Show-Help
    }
    "-h" {
        Show-Help
    }
    "--help" {
        Show-Help
    }
    default {
         function Resolve-FrameworkRoot([string]`$FallbackRoot) {
             `$probe = (Get-Location).Path
             while (`$probe) {
                 `$localRuntime = Join-Path `$probe "skills/workflow-runtime"
                 `$mirrorRuntime = Join-Path `$probe ".agents/skills/workflow-runtime"
                 if (Test-Path (Join-Path `$localRuntime "workflow_runtime/__main__.py")) { return `$probe }
                 if (Test-Path (Join-Path `$mirrorRuntime "workflow_runtime/__main__.py")) { return `$probe }
                 `$parent = Split-Path -Parent `$probe
                 if (`$parent -eq `$probe) { break }
                 `$probe = `$parent
             }
             return `$FallbackRoot
         }

         `$resolvedRoot = Resolve-FrameworkRoot `$FrameworkRoot
         `$runtimeRoot = Join-Path `$resolvedRoot "skills/workflow-runtime"
         if (-not (Test-Path (Join-Path `$runtimeRoot "workflow_runtime/__main__.py"))) {
             `$runtimeRoot = Join-Path `$resolvedRoot ".agents/skills/workflow-runtime"
         }
         `$oldPythonPath = `$env:PYTHONPATH
         `$oldFrameworkRoot = `$env:AIWF_FRAMEWORK_ROOT
         `$env:AIWF_FRAMEWORK_ROOT = `$resolvedRoot
         `$env:PYTHONPATH = `$runtimeRoot
         `$runtimeArgs = @(`$Command) + @(`$args)
         python -m workflow_runtime @runtimeArgs
         `$exitCode = `$LASTEXITCODE
         `$env:PYTHONPATH = `$oldPythonPath
         if (`$null -eq `$oldFrameworkRoot) { Remove-Item Env:AIWF_FRAMEWORK_ROOT -ErrorAction SilentlyContinue }
         else { `$env:AIWF_FRAMEWORK_ROOT = `$oldFrameworkRoot }
         exit `$exitCode
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
