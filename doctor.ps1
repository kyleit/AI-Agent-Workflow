# ==============================================================================
# AI Skill Framework Diagnostic Tool (doctor)
# Verifies the global and local framework installation state for Windows.
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$NoFix
)

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

$global:StatusPass = 0
$global:StatusWarn = 0
$global:StatusFail = 0
$AutoFix = -not ($CheckOnly -or $NoFix)

function Check-Item ($label, $conditionBlock, $rec) {
    $res = & $conditionBlock
    if ($res) {
        Log-Success "  [PASS] $label"
    }
    else {
        if ($rec -eq "critical") {
            Log-Error "  [FAIL] $label"
            $global:StatusFail++
        }
        else {
            Log-Warn "  [WARN] $label"
            Log-Warn "         -> Recommendation: $rec"
            $global:StatusWarn++
        }
    }
}

function Invoke-SafeRepair ($label, [scriptblock]$Action) {
    if (-not $AutoFix) {
        Log-Warn "  [SKIP] $label (auto-fix disabled)"
        return $false
    }
    Log-Info "  [FIX] $label"
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "Command exited with code $LASTEXITCODE"
        }
        Log-Success "  [FIXED] $label"
        return $true
    }
    catch {
        Log-Warn "  [WARN] Auto-repair failed: $label. $_"
        return $false
    }
}

function Get-PythonCommand {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $py) { return "python" }
    $py3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -ne $py3) { return "python3" }
    return $null
}

function Ensure-PythonRuntimeDeps {
    $py = Get-PythonCommand
    if ($null -eq $py) {
        Log-Warn "  [WARN] Python is missing; install Python 3.11+ then rerun aiwf doctor."
        $global:StatusWarn++
        return
    }
    $probe = @'
import importlib.util

mods = {
    "yaml": "pyyaml",
    "psutil": "psutil",
    "pytest": "pytest",
}

print(" ".join(pkg for mod, pkg in mods.items() if importlib.util.find_spec(mod) is None))
'@
    $missingOutput = $null
    try {
        $missingOutput = $probe | & $py - 2>$null
    }
    catch {
        $missingOutput = $null
    }

    if ($LASTEXITCODE -ne 0 -or $null -eq $missingOutput) {
        $missing = ""
    }
    else {
        $missing = ($missingOutput -join " ").Trim()
    }

    if ([string]::IsNullOrWhiteSpace($missing)) {
        Log-Success "  [PASS] Python runtime packages available (pyyaml, psutil, pytest)"
        return
    }
    Log-Warn "  [WARN] Missing Python runtime packages: $missing"
    $global:StatusWarn++
    $packages = $missing -split "\s+"
    Invoke-SafeRepair "Installing Python runtime packages: $missing" {
        & $py -m pip install --user --upgrade @packages
    } | Out-Null
}

function Test-RuntimeCliSmoke {
    $py = Get-PythonCommand
    if ($null -eq $py) { return $false }
    $oldPythonPath = $env:PYTHONPATH
    $runtimePath = Join-Path $ScriptDir "skills/workflow-runtime"
    if ([string]::IsNullOrEmpty($oldPythonPath)) {
        $env:PYTHONPATH = $runtimePath
    }
    else {
        $env:PYTHONPATH = "$runtimePath;$oldPythonPath"
    }
    try {
        & $py -m workflow_runtime --help | Out-Null
        return $LASTEXITCODE -eq 0
    }
    finally {
        $env:PYTHONPATH = $oldPythonPath
    }
}

function Install-CurrentPackage {
    $installScript = Join-Path $ScriptDir "install.ps1"
    if (Test-Path $installScript) {
        & $installScript -Force
    }
    else {
        & aiwf install -Force
    }
}

function Update-CurrentPackage {
    $updateScript = Join-Path $ScriptDir "update.ps1"
    if (Test-Path $updateScript) {
        & $updateScript -Force
    }
    else {
        & aiwf update -Force
    }
}

Write-Host "=================================================="
Write-Host "      AI Skill Framework Doctor Diagnostic        "
Write-Host "=================================================="

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }
if ($AutoFix) {
    Log-Info "Safe auto-repair is ENABLED. Use -CheckOnly or -NoFix to inspect without changes."
}
else {
    Log-Info "Safe auto-repair is DISABLED."
}

$ManifestPath = Join-Path $ScriptDir "MANIFEST.json"

function Test-AiwfProjectInstalled {
    return (Test-Path $InstallTarget) `
        -and (Test-Path (Join-Path $InstallTarget "AI_RULES.md")) `
        -and (Test-Path (Join-Path $InstallTarget "MANIFEST.json")) `
        -and (Test-Path (Join-Path $InstallTarget "skills"))
}

# Check 1: MANIFEST.json present
Check-Item "MANIFEST.json exists in framework" { Test-Path $ManifestPath } "critical"

# Load manifest
$Version = ""
$SkillDir = "skills"
$TemplateDir = "templates"
$InstallTarget = ".agents"

if (Test-Path $ManifestPath) {
    try {
        $Manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
        $Version = $Manifest.version
        $SkillDir = $Manifest.skill_directory
        $TemplateDir = $Manifest.template_directory
        $InstallTarget = $Manifest.installation_target
    }
    catch {}
}

# Check 2: Version is readable
Check-Item "Framework version is readable (v$Version)" { -not [string]::IsNullOrEmpty($Version) } "critical"

# Check 3: Skills directory exists
Check-Item "Skills directory exists ($SkillDir/)" { Test-Path (Join-Path $ScriptDir $SkillDir) } "critical"

# Check 4: Templates directory exists
Check-Item "Templates directory exists ($TemplateDir/)" { Test-Path (Join-Path $ScriptDir $TemplateDir) } "critical"

# Check 5: CLI wrapper available in PATH
$CLIPath = Get-Command "aiwf" -ErrorAction SilentlyContinue
Check-Item "aiwf CLI wrapper is available in PATH" { $null -ne $CLIPath } "Add %LOCALAPPDATA%\aiwf to your Environment Variables PATH."

Ensure-PythonRuntimeDeps
if (Test-RuntimeCliSmoke) {
    Log-Success "  [PASS] Runtime CLI dependency readiness"
}
else {
    Log-Warn "  [WARN] Runtime CLI dependency readiness"
    Log-Warn "         -> Recommendation: Rerun 'aiwf doctor' after Python package installation completes, or reinstall with './bootstrap.ps1'."
    $global:StatusWarn++
}

# Check 5.5: API Keys for AI Providers (Gemini / Anthropic)
$HasGeminiKey = -not [string]::IsNullOrEmpty($env:GEMINI_API_KEY)
$HasAnthropicKey = -not [string]::IsNullOrEmpty($env:ANTHROPIC_API_KEY)
Check-Item "AI Provider API Key is configured (Gemini or Anthropic)" { $HasGeminiKey -or $HasAnthropicKey } "Set either GEMINI_API_KEY or ANTHROPIC_API_KEY environment variable to use AI coding skills."

# Check 6: Check active project environment
function Test-GitWorkTree {
    $gitExists = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitExists) {
        return $false
    }
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Get-GitRoot {
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        return $null
    }
    return $root.Trim()
}

$IsGit = $false
$ProjectRoot = "."

if (Test-GitWorkTree) {
    $IsGit = $true
    $ProjectRoot = Get-GitRoot
} elseif (Test-Path ".git") {
    $IsGit = $true
    $ProjectRoot = "."
}

if ($IsGit) {
    Set-Location $ProjectRoot
    Log-Info "Active Git repository detected at $ProjectRoot."
    
    if (-not (Test-AiwfProjectInstalled)) {
        Invoke-SafeRepair "Installing AIWF into active project from current package" {
            Install-CurrentPackage
        } | Out-Null
    }
    Check-Item "Framework installed in active project ($InstallTarget/)" { Test-AiwfProjectInstalled } "Run 'aiwf install' to deploy framework skills into this project."
               
    if (Test-Path $InstallTarget) {
        if (-not (Test-Path (Join-Path $InstallTarget "AI_RULES.md")) -or -not (Test-Path (Join-Path $InstallTarget "MANIFEST.json"))) {
            Invoke-SafeRepair "Restoring missing project AIWF files from current package" {
                Update-CurrentPackage
            } | Out-Null
        }
        Check-Item "AI_RULES.md present in project" { Test-Path (Join-Path $InstallTarget "AI_RULES.md") } "Run 'aiwf update -Force' to restore missing rules file."
                   
        Check-Item "MANIFEST.json present in project" { Test-Path (Join-Path $InstallTarget "MANIFEST.json") } "Run 'aiwf update -Force' to restore missing manifest."
    }
}
else {
    Log-Info "No active Git project detected at current path. Skipping local workspace check."
}

# Diagnosing global project registry
if (Get-Command "aiwf" -ErrorAction SilentlyContinue) {
    Log-Info "Verifying AIWF Registry via aiwf CLI..."
    & aiwf registry --format json | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "Failed to diagnose project registry."
        $global:StatusWarn++
    }
} else {
    Log-Warn "aiwf CLI not found. Skipping registry doctor."
    $global:StatusWarn++
}

Write-Host "=================================================="
Write-Host "Diagnostic Summary:"
Write-Host "  Errors:   $global:StatusFail"
Write-Host "  Warnings: $global:StatusWarn"
Write-Host "=================================================="

if ($global:StatusFail -gt 0) {
    Log-Error "STATUS: ERROR"
    Log-Error "Please fix critical errors to restore framework capabilities."
    exit 1
}
elseif ($global:StatusWarn -gt 0) {
    Log-Warn "STATUS: WARNING"
    Log-Warn "Review recommendations to optimize your workspace."
    exit 0
}
else {
    Log-Success "STATUS: PASS"
    Log-Success "AI Skill Framework is healthy and ready to use."
    exit 0
}
