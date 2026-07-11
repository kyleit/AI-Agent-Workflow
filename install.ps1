<#
.SYNOPSIS
    AI Skill Framework Installer for Windows PowerShell and PowerShell Core.
.DESCRIPTION
    Installs the framework files (AI_RULES.md, MANIFEST.json, skills/, templates/) into the target project's .agents/ directory.
.PARAMETER Force
    Overwrites existing files without prompting.
.EXAMPLE
    .\install.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$Force,
    [string]$Permission = $null
)

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Error "[ERROR] $msg" }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# 1. Verify current directory is a Git project
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

if (-not $IsGit) {
    $gitExists = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitExists) {
        Log-Error "git command line tool is missing, and no .git folder/file found."
    } else {
        Log-Error "The current directory is not a Git repository."
        Log-Error "The AI Skill Framework must be installed at the root of a Git project."
    }
    exit 1
}

Set-Location $ProjectRoot
Log-Success "Git repository detected."
Log-Info "Project root: $ProjectRoot"
Log-Info "Installing AI Skill Framework into $ProjectRoot/.agents"

# Locate the framework package directory (where this script lives)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

$ManifestPath = Join-Path $ScriptDir "MANIFEST.json"
if (-not (Test-Path $ManifestPath)) {
    Log-Error "MANIFEST.json not found in source directory ($ScriptDir)."
    exit 1
}

# 2. Read MANIFEST.json
try {
    $Manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
}
catch {
    Log-Error "Failed to parse MANIFEST.json in source directory. Details: $_"
    exit 1
}

$InstallTarget = $Manifest.installation_target
$SkillDir = $Manifest.skill_directory
$TemplateDir = $Manifest.template_directory
$Version = $Manifest.version

if ([string]::IsNullOrEmpty($InstallTarget) -or [string]::IsNullOrEmpty($SkillDir) -or [string]::IsNullOrEmpty($TemplateDir)) {
    Log-Error "Invalid or corrupt MANIFEST.json in source directory."
    exit 1
}

Log-Info "Installing AI Skill Framework v$Version..."
Log-Info "Target Directory: $InstallTarget/"

# 3. Create target directory if missing
if (-not (Test-Path $InstallTarget)) {
    Log-Info "Creating target directory $InstallTarget/"
    New-Item -ItemType Directory -Path $InstallTarget -Force | Out-Null
}

# Helper to copy with overwrite check
function Copy-ItemWithCheck {
    param(
        [string]$Src,
        [string]$Dest,
        [bool]$IsDir
    )

    if (Test-Path $Dest) {
        if ($Force) {
            Log-Info "Overwriting: $Dest (forced)"
            Remove-Item -Path $Dest -Recurse -Force | Out-Null
            Copy-Item -Path $Src -Destination $Dest -Recurse -Force | Out-Null
        }
        else {
            $Choice = Read-Host "[PROMPT] $Dest already exists. Overwrite? (y/N)"
            if ($Choice -match "^(y|yes)$") {
                Log-Info "Overwriting: $Dest"
                Remove-Item -Path $Dest -Recurse -Force | Out-Null
                Copy-Item -Path $Src -Destination $Dest -Recurse -Force | Out-Null
            }
            else {
                Log-Warn "Skipped: $Dest"
            }
        }
    }
    else {
        Log-Info "Creating: $Dest"
        Copy-Item -Path $Src -Destination $Dest -Recurse -Force | Out-Null
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
11. Absolute Path Prohibition Policy

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

# 4. Copy required files/directories
Merge-AgentsBlock -FilePath (Join-Path $InstallTarget "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")
Copy-ItemWithCheck -Src (Join-Path $ScriptDir "AI_RULES.md") -Dest (Join-Path $InstallTarget "AI_RULES.md") -IsDir $false
Copy-ItemWithCheck -Src (Join-Path $ScriptDir "SKILLS.md") -Dest (Join-Path $InstallTarget "SKILLS.md") -IsDir $false
Copy-ItemWithCheck -Src (Join-Path $ScriptDir $SkillDir) -Dest (Join-Path $InstallTarget $SkillDir) -IsDir $true
Copy-ItemWithCheck -Src (Join-Path $ScriptDir $TemplateDir) -Dest (Join-Path $InstallTarget $TemplateDir) -IsDir $true
Copy-ItemWithCheck -Src (Join-Path $ScriptDir "agents") -Dest (Join-Path $InstallTarget "agents") -IsDir $true
Copy-ItemWithCheck -Src (Join-Path $ScriptDir "runtime") -Dest (Join-Path $InstallTarget "runtime") -IsDir $true
$DocsTargetDir = Join-Path $InstallTarget "docs"
if (-not (Test-Path $DocsTargetDir)) {
    New-Item -ItemType Directory -Path $DocsTargetDir -Force | Out-Null
}
Copy-ItemWithCheck -Src (Join-Path (Join-Path $ScriptDir "docs") "release-guide.md") -Dest (Join-Path $DocsTargetDir "release-guide.md") -IsDir $false
Copy-ItemWithCheck -Src $ManifestPath -Dest (Join-Path $InstallTarget "MANIFEST.json") -IsDir $false

# Initialize a clean .session.json if it doesn't exist
$SessionPath = Join-Path $InstallTarget ".session.json"
if (-not (Test-Path $SessionPath)) {
    Log-Info "Initializing default .session.json for visualizer UI..."
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
    "type": "FEAT",
    "id": "FEAT-001",
    "title": "Initial Scaffolding"
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
  "blueprint": {
    "path": "",
    "exists": false,
    "approved": false,
    "approved_at": "",
    "approved_by": ""
  },
  "suggestion_gate": {
    "active": false,
    "raw_request": "",
    "classification": "",
    "recommended_skill": "",
    "options": [],
    "status": "idle"
  },
  "checkpoint": 1,
  "status": "completed",
  "current_skill": "initialize-workflow",
  "current_command": "init",
  "current_step": "Initialization Complete",
  "current_logs": [
    "> Initialization completed successfully."
  ],
  "suggested_next_skill": "project-discovery",
  "suggested_next_command": "discover",
  "context_health": "healthy"
}
'@
    Set-Content -Path $SessionPath -Value $DefaultSession -Encoding UTF8
}

# 5. Validation and Summary
$MissingFiles = 0
$RequiredFiles = @("AGENTS.md", "AI_RULES.md", "MANIFEST.json", $SkillDir, $TemplateDir, "agents", "runtime", "docs/release-guide.md")
foreach ($File in $RequiredFiles) {
    $CheckPath = Join-Path $InstallTarget $File
    if (-not (Test-Path $CheckPath)) {
        Log-Error "Validation failed: Missing $CheckPath"
        $MissingFiles++
    }
}

if ($MissingFiles -gt 0) {
    Log-Error "Installation was incomplete. Please review warnings above."
    exit 1
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 (Join-Path (Join-Path $InstallTarget $SkillDir) "workflow-runtime/scripts/workflow_runtime.py") $InitArgs
    python3 (Join-Path (Join-Path $InstallTarget $SkillDir) "workflow-runtime/scripts/workflow_runtime.py") registry register --source install --framework-root $ScriptDir
}

Log-Success "AI Skill Framework v$VERSION has been successfully installed!"
Write-Host "--------------------------------------------------"
Write-Host "Installation Summary:"
Write-Host "  Location:  $InstallTarget/"
Write-Host "  Rules:     $(Join-Path $InstallTarget 'AI_RULES.md')"
Write-Host "  Skills:    $(Join-Path $InstallTarget $SkillDir)/"
Write-Host "  Templates: $(Join-Path $InstallTarget $TemplateDir)/"
Write-Host "--------------------------------------------------"
Log-Info "To use these skills, make sure your AI Agent workspace points to $InstallTarget/."
