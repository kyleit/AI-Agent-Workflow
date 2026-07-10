# ==============================================================================
# AI Skill Framework Diagnostic Tool (doctor)
# Verifies the global and local framework installation state for Windows.
# ==============================================================================

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

$global:StatusPass = 0
$global:StatusWarn = 0
$global:StatusFail = 0

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

Write-Host "=================================================="
Write-Host "      AI Skill Framework Doctor Diagnostic        "
Write-Host "=================================================="

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

$ManifestPath = Join-Path $ScriptDir "MANIFEST.json"

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
    
    Check-Item "Framework installed in active project ($InstallTarget/)" { Test-Path $InstallTarget } "Run 'aiwf install' to deploy framework skills into this project."
               
    if (Test-Path $InstallTarget) {
        Check-Item "AI_RULES.md present in project" { Test-Path (Join-Path $InstallTarget "AI_RULES.md") } "Run 'aiwf update -Force' to restore missing rules file."
                   
        Check-Item "MANIFEST.json present in project" { Test-Path (Join-Path $InstallTarget "MANIFEST.json") } "Run 'aiwf update -Force' to restore missing manifest."
    }
}
else {
    Log-Info "No active Git project detected at current path. Skipping local workspace check."
}

# Diagnosing global project registry
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    Log-Info "Diagnosing global project registry..."
    python3 (Join-Path $ScriptDir "skills/workflow-runtime/scripts/workflow_runtime.py") registry doctor
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
