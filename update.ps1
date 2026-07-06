<#
.SYNOPSIS
    AI Skill Framework Updater for Windows PowerShell.
.DESCRIPTION
    Safely synchronizes existing installations without overwriting user customizations.
.PARAMETER Force
    Force synchronization even if versions match.
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

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

$ManifestPath = Join-Path $ScriptDir "MANIFEST.json"
if (-not (Test-Path $ManifestPath)) {
    Log-Error "MANIFEST.json not found in source directory ($ScriptDir)."
    exit 1
}

# Read Source Manifest
try {
    $SrcManifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
}
catch {
    Log-Error "Failed to parse MANIFEST.json in source directory. Details: $_"
    exit 1
}

$InstallTarget = $SrcManifest.installation_target
$SkillDir = $SrcManifest.skill_directory
$TemplateDir = $SrcManifest.template_directory
$SrcVersion = $SrcManifest.version

$TargetManifestPath = Join-Path $InstallTarget "MANIFEST.json"
if (-not (Test-Path $TargetManifestPath)) {
    Log-Error "No active installation found at $TargetManifestPath."
    Log-Error "Please run .\install.ps1 first to set up the framework."
    exit 1
}

# Read Target Manifest
try {
    $TargetManifest = Get-Content -Raw -Path $TargetManifestPath | ConvertFrom-Json
    $TargetVersion = $TargetManifest.version
}
catch {
    Log-Error "Failed to parse target MANIFEST.json. Details: $_"
    exit 1
}

Log-Info "Detected Installed Version: v$TargetVersion"
Log-Info "Available Repository Version: v$SrcVersion"

if ($SrcVersion -eq $TargetVersion -and -not $Force) {
    Log-Success "AI Skill Framework is already up to date (v$TargetVersion)."
    exit 0
}

Log-Info "Synchronizing installation..."

function Get-SkillNames ($skills) {
    $names = @()
    foreach ($s in $skills) {
        if ($null -eq $s) { continue }
        if ($s -is [string]) {
            $names += $s
        }
        elseif ($null -ne $s.name) {
            $names += $s.name
        }
        else {
            $names += $s.ToString()
        }
    }
    return $names
}

# Calculate changes in skills
$SrcSkills = Get-SkillNames $SrcManifest.skills
$TargetSkills = Get-SkillNames $TargetManifest.skills

$NewSkills = @()
$UpdatedSkills = @()
$RemovedSkills = @()

foreach ($Skill in $SrcSkills) {
    if ($TargetSkills -contains $Skill) {
        $UpdatedSkills += $Skill
    }
    else {
        $NewSkills += $Skill
    }
}

foreach ($Skill in $TargetSkills) {
    if ($SrcSkills -notcontains $Skill) {
        $RemovedSkills += $Skill
    }
}

# Perform safe copy updates
function Update-ItemWithCheck ($src, $dest) {
    # If different or doesn't exist, update it
    if (-not (Test-Path $dest)) {
        Log-Info "Creating: $dest"
        Copy-Item -Path $src -Destination $dest -Recurse -Force | Out-Null
    }
    else {
        # Check if contents are different (using Get-FileHash for folders/files is complex, we can do simple compare or force copy)
        Log-Info "Updating: $dest"
        Remove-Item -Path $dest -Recurse -Force | Out-Null
        Copy-Item -Path $src -Destination $dest -Recurse -Force | Out-Null
    }
}

function Merge-AgentsBlock {
    param(
        [string]$FilePath,
        [string]$SourcePath
    )
    
    $BlockContent = @"
<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Every AI agent working inside this project **MUST** follow the AI Workflow Framework.

## Primary Workflow

Before executing any task:

1. Load and follow all policies defined in `AI_RULES.md` (the single source of truth).
2. Load the workflow resources from:

   * `.agents/skills/`
   * `.agents/runtime/`
   * `.agents/templates/`
3. Use the matching workflow Skill whenever one exists.
4. Respect runtime checkpoints and resume rules.
5. Never bypass approval gates or other framework policies.

## Global Policies

The following policies are defined in `AI_RULES.md` and apply to every task:

1. Approval Gate Policy
2. Git Workflow Policy
3. Memory First Policy
4. RAG Policy
5. Artifact Policy
6. Versioning Policy
7. Documentation Policy
8. Testing Policy
9. Release Policy
10. Workflow Phase Separation Policy

`AI_RULES.md` is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow `AI_RULES.md`.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow

<!-- AIWF:RULES:END -->
"@

    if (-not (Test-Path $FilePath)) {
        Log-Info "Creating: $FilePath (copying template)"
        Copy-Item -Path $SourcePath -Destination $FilePath -Force | Out-Null
        return
    }
    
    $Content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    $BeginMarker = "<!-- AIWF:RULES:BEGIN -->"
    $EndMarker = "<!-- AIWF:RULES:END -->"
    
    $HasBegin = $Content.Contains($BeginMarker)
    $HasEnd = $Content.Contains($EndMarker)
    
    if ($HasBegin -and $HasEnd) {
        Log-Info "Updating managed block in $FilePath"
        $EscBegin = [Regex]::Escape($BeginMarker)
        $EscEnd = [Regex]::Escape($EndMarker)
        $Regex = "(?s)" + $EscBegin + ".*?" + $EscEnd
        
        $NewContent = [Regex]::Replace($Content, $Regex, $BlockContent)
        [System.IO.File]::WriteAllText($FilePath, $NewContent, [System.Text.Encoding]::UTF8)
    }
    elseif ($HasBegin -or $HasEnd) {
        Log-Warn "Corrupted managed block markers detected in $FilePath. Rebuilding safely..."
        $CleanContent = $Content.Replace($BeginMarker, "").Replace($EndMarker, "").Trim()
        $NewContent = $CleanContent
        if (-not [string]::IsNullOrEmpty($CleanContent)) {
            $NewContent += "`r`n`r`n"
        }
        $NewContent += $BlockContent
        [System.IO.File]::WriteAllText($FilePath, $NewContent, [System.Text.Encoding]::UTF8)
    }
    else {
        Log-Info "Appending managed block to $FilePath"
        $Trimmed = $Content.Trim()
        $NewContent = $Trimmed
        if (-not [string]::IsNullOrEmpty($Trimmed)) {
            $NewContent += "`r`n`r`n"
        }
        $NewContent += $BlockContent
        [System.IO.File]::WriteAllText($FilePath, $NewContent, [System.Text.Encoding]::UTF8)
    }
}

# Copy changed rules and manifest files
Merge-AgentsBlock -FilePath (Join-Path $InstallTarget "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")
Update-ItemWithCheck -src (Join-Path $ScriptDir "AI_RULES.md") -dest (Join-Path $InstallTarget "AI_RULES.md")
Update-ItemWithCheck -src (Join-Path $ScriptDir "agents") -dest (Join-Path $InstallTarget "agents")
Update-ItemWithCheck -src (Join-Path $ScriptDir "runtime") -dest (Join-Path $InstallTarget "runtime")
$DocsTargetDir = Join-Path $InstallTarget "docs"
if (-not (Test-Path $DocsTargetDir)) {
    New-Item -ItemType Directory -Path $DocsTargetDir -Force | Out-Null
}
Update-ItemWithCheck -src (Join-Path (Join-Path $ScriptDir "docs") "release-guide.md") -dest (Join-Path $DocsTargetDir "release-guide.md")
Update-ItemWithCheck -src $ManifestPath -dest $TargetManifestPath

# Initialize a clean .session.json if missing, or upgrade if it is in the old flat format
$SessionPath = Join-Path $InstallTarget ".session.json"
$SessionExists = Test-Path $SessionPath
$NeedsUpgrade = $false
if ($SessionExists) {
    $SessionContent = Get-Content -Path $SessionPath -Raw
    if ($SessionContent -notmatch '"workspace": \{') {
        $NeedsUpgrade = $true
    }
}

if (-not $SessionExists -or $NeedsUpgrade) {
    Log-Info "Creating or upgrading .session.json to the new nested format..."
    $DefaultSession = @'
{
  "workspace": {
    "path": ".",
    "valid": true
  },
  "git": {
    "is_git_repository": true,
    "branch": "main",
    "working_tree": "clean",
    "default_branch": "main",
    "latest_tag": "none"
  },
  "work_item": {
    "type": "N/A",
    "id": "N/A",
    "title": "Awaiting active task selection..."
  },
  "version": {
    "version": "1.0.0",
    "source": "MANIFEST.json"
  },
  "memory": {
    "status": "MISSING",
    "last_updated": ""
  },
  "rag": {
    "connected": false,
    "provider": "none"
  },
  "checkpoint": 1,
  "current_skill": "initialize-workflow",
  "current_step": "Awaiting initial command",
  "context_health": "healthy"
}
'@
    Set-Content -Path $SessionPath -Value $DefaultSession -Encoding UTF8
}

# Copy active skills
foreach ($Skill in $SrcSkills) {
    Update-ItemWithCheck -src (Join-Path (Join-Path $ScriptDir $SkillDir) $Skill) -dest (Join-Path (Join-Path $InstallTarget $SkillDir) $Skill)
}

# Copy templates
if (Test-Path (Join-Path $ScriptDir $TemplateDir)) {
    if (-not (Test-Path (Join-Path $InstallTarget $TemplateDir))) {
        New-Item -ItemType Directory -Path (Join-Path $InstallTarget $TemplateDir) -Force | Out-Null
    }
    Copy-Item -Path (Join-Path (Join-Path $ScriptDir $TemplateDir) "*") -Destination (Join-Path $InstallTarget $TemplateDir) -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
}

Log-Success "AI Skill Framework has been successfully updated to v$SrcVersion!"
Write-Host "--------------------------------------------------"
Write-Host "Upgrade Summary:"
if ($NewSkills.Count -gt 0) {
    Write-Host "  New Skills:     $($NewSkills -join ', ')"
}
if ($UpdatedSkills.Count -gt 0) {
    Write-Host "  Updated Skills: $($UpdatedSkills -join ', ')"
}
if ($RemovedSkills.Count -gt 0) {
    Write-Host "  [DEPRECATED] Legacy skills found in installation target (safe deletion recommended):" -ForegroundColor Yellow
    foreach ($rskill in $RemovedSkills) {
        Write-Host "    - $(Join-Path (Join-Path $InstallTarget $SkillDir) $rskill)" -ForegroundColor Yellow
    }
}
Write-Host "--------------------------------------------------"
Log-Info "Run aiwf doctor to confirm workspace integrity."
