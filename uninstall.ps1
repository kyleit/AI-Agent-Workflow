<#
.SYNOPSIS
    AI Skill Framework Uninstaller for Windows PowerShell.
.DESCRIPTION
    Safely removes only framework-managed files without deleting user customizations.
.PARAMETER Force
    Skip confirmation prompts.
#>

[CmdletBinding()]
param(
    [switch]$Force
)

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Error "[ERROR] $msg" }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

$InstallTarget = ".agents"
$TargetManifestPath = Join-Path $InstallTarget "MANIFEST.json"

if (-not (Test-Path $TargetManifestPath)) {
    Log-Error "No active installation manifest found at $TargetManifestPath."
    exit 1
}

# Read target manifest
try {
    $TargetManifest = Get-Content -Raw -Path $TargetManifestPath | ConvertFrom-Json
    $Version = $TargetManifest.version
    $SkillDir = $TargetManifest.skill_directory
    $TemplateDir = $TargetManifest.template_directory
    $Skills = $TargetManifest.skills
}
catch {
    Log-Error "Failed to parse target manifest. Details: $_"
    exit 1
}

# Prompt for confirmation
if (-not $Force) {
    $Choice = Read-Host "[PROMPT] Are you sure you want to uninstall AI Skill Framework v$Version? (y/N)"
    if ($Choice -notmatch "^(y|yes)$") {
        Log-Info "Uninstallation cancelled."
        exit 0
    }
}

Log-Info "Removing framework-managed files..."

$RemovedFilesCount = 0

# 1. Remove individual skills
if (Test-Path (Join-Path $InstallTarget $SkillDir)) {
    foreach ($Skill in $Skills) {
        $SkillPath = Join-Path $InstallTarget $SkillDir $Skill
        if (Test-Path $SkillPath) {
            Log-Info "Removing skill: $SkillPath"
            Remove-Item -Path $SkillPath -Recurse -Force | Out-Null
            $RemovedFilesCount++
        }
    }

    # Delete skills/ directory if it is empty
    $RemainingItems = Get-ChildItem -Path (Join-Path $InstallTarget $SkillDir) -ErrorAction SilentlyContinue
    if ($null -eq $RemainingItems -or $RemainingItems.Count -eq 0) {
        Remove-Item -Path (Join-Path $InstallTarget $SkillDir) -Force | Out-Null
    }
    else {
        Log-Warn "Skills folder contains user-customized skills. Folder was not deleted."
    }
}

# 2. Remove templates
$TemplatePath = Join-Path $InstallTarget $TemplateDir
if (Test-Path $TemplatePath) {
    Log-Info "Removing templates: $TemplatePath"
    Remove-Item -Path $TemplatePath -Recurse -Force | Out-Null
    $RemovedFilesCount++
}

# 3. Remove rules, agents, runtime, and manifest
$RulesPath = Join-Path $InstallTarget "AI_RULES.md"
if (Test-Path $RulesPath) {
    Log-Info "Removing rules: $RulesPath"
    Remove-Item -Path $RulesPath -Force | Out-Null
    $RemovedFilesCount++
}

$AgentsPath = Join-Path $InstallTarget "agents"
if (Test-Path $AgentsPath) {
    Log-Info "Removing agents definition directory: $AgentsPath"
    Remove-Item -Path $AgentsPath -Recurse -Force | Out-Null
    $RemovedFilesCount++
}

$RuntimePath = Join-Path $InstallTarget "runtime"
if (Test-Path $RuntimePath) {
    Log-Info "Removing runtime directory: $RuntimePath"
    Remove-Item -Path $RuntimePath -Recurse -Force | Out-Null
    $RemovedFilesCount++
}

$ReleaseGuidePath = Join-Path (Join-Path $InstallTarget "docs") "release-guide.md"
if (Test-Path $ReleaseGuidePath) {
    Log-Info "Removing release guide: $ReleaseGuidePath"
    Remove-Item -Path $ReleaseGuidePath -Force | Out-Null
    $RemovedFilesCount++
    $DocsDir = Join-Path $InstallTarget "docs"
    $RemainingDocs = Get-ChildItem -Path $DocsDir -ErrorAction SilentlyContinue
    if ($null -eq $RemainingDocs -or $RemainingDocs.Count -eq 0) {
        Remove-Item -Path $DocsDir -Force | Out-Null
    }
}

if (Test-Path $TargetManifestPath) {
    Log-Info "Removing manifest: $TargetManifestPath"
    Remove-Item -Path $TargetManifestPath -Force | Out-Null
    $RemovedFilesCount++
}

# 4. Remove .agents folder if empty
if (Test-Path $InstallTarget) {
    $RemainingAgents = Get-ChildItem -Path $InstallTarget -ErrorAction SilentlyContinue
    if ($null -eq $RemainingAgents -or $RemainingAgents.Count -eq 0) {
        Remove-Item -Path $InstallTarget -Force | Out-Null
        Log-Info "Removed empty target directory: $InstallTarget/"
    }
    else {
        Log-Warn "$InstallTarget/ contains other files (e.g. project memory). Directory was not deleted."
    }
}

Log-Success "AI Skill Framework v$Version uninstalled successfully!"
Write-Host "--------------------------------------------------"
Write-Host "Uninstall Summary:"
Write-Host "  Removed $RemovedFilesCount framework components."
Write-Host "  User configurations and custom memory files were preserved."
Write-Host "--------------------------------------------------"
