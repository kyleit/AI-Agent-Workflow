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
    [string]$Permission = $null,
    [ValidateSet("project", "global")]
    [string]$Scope = "project",
    [switch]$AssumeGlobal,
    [switch]$FullInstall,
    [switch]$Reclaim
)

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Error "[ERROR] $msg" }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# Resolve a Python interpreter (>=3.9) once for scope-helper calls.
$PY = $null
foreach ($cand in @("python3", "python", "py")) {
    $found = Get-Command $cand -ErrorAction SilentlyContinue
    if ($found) {
        & $cand -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $PY = $cand; break }
    }
}
$GlobalHomeAgents = Join-Path $HOME ".agents"
# Managed-block rendering mode (full self-contained vs stub pointer). Set per-run.
$script:BlockMode = "full"

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

# Global scope installs to ~/.agents and does not require a Git project.
if ($Scope -eq "project") {
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
} else {
    $ProjectRoot = (Get-Location).Path
    Log-Info "Global scope: installing shared framework into $GlobalHomeAgents"
}

# Locate the framework package directory (where this script lives)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }
$ScopeHelper = Join-Path (Join-Path $ScriptDir "install-lib") "aiwf_scope.py"

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

function Remove-InstalledTransientFiles {
    param([string]$Root)

    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    $transientNames = @("scratch", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory -ErrorAction SilentlyContinue |
        Where-Object { $transientNames -contains $_.Name } |
        ForEach-Object {
            $candidate = $_.FullName
            if ($candidate.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                Remove-Item -LiteralPath $candidate -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
}

function Merge-AgentsBlock {
    param(
        [string]$FilePath,
        [string]$SourcePath
    )

    # Preferred: delegate to the shared scope helper so full/stub block rendering
    # and idempotent merging are identical across install.sh and install.ps1.
    if ($PY -and (Test-Path $ScopeHelper)) {
        & $PY $ScopeHelper apply-block --file $FilePath --mode $script:BlockMode --home $GlobalHomeAgents
        if ($LASTEXITCODE -eq 0) {
            Log-Info "Applied AIWF '$($script:BlockMode)' rules block to $FilePath"
            return
        }
        Log-Warn "Scope helper failed for $FilePath; falling back to inline full block."
    }

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

GitHub Repository: https://github.com/your-org/AI-Agent-Workflow

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

function Test-ValidSkillMd {
    param(
        [string]$SkillMdPath,
        [string]$SkillName
    )
    if (-not (Test-Path $SkillMdPath)) { return $true }
    $bytes = [System.IO.File]::ReadAllBytes($SkillMdPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Log-Warn "SKIP ${SkillName}: SKILL.md has UTF-8 BOM - frontmatter unreadable"
        return $false
    }
    $content = [System.IO.File]::ReadAllText($SkillMdPath, [System.Text.Encoding]::UTF8)
    if (-not ($content -match '(?s)^---\r?\n(.*?)\r?\n---')) {
        Log-Warn "SKIP ${SkillName}: SKILL.md has no frontmatter delimiter"
        return $false
    }
    $fm = $Matches[1]
    if (-not ($fm -match '(?m)^name:')) {
        Log-Warn "SKIP ${SkillName}: SKILL.md missing 'name:' in frontmatter"
        return $false
    }
    if (-not ($fm -match '(?m)^description:')) {
        Log-Warn "SKIP ${SkillName}: SKILL.md missing 'description:' in frontmatter"
        return $false
    }
    return $true
}

function Copy-SharedPayload {
    param([string]$Target)
    Copy-ItemWithCheck -Src (Join-Path $ScriptDir "AI_RULES.md") -Dest (Join-Path $Target "AI_RULES.md") -IsDir $false
    $skillsMd = Join-Path $ScriptDir "SKILLS.md"
    if (Test-Path $skillsMd) { Copy-ItemWithCheck -Src $skillsMd -Dest (Join-Path $Target "SKILLS.md") -IsDir $false }

    $SrcSkillDir = Join-Path $ScriptDir $SkillDir
    $DestSkillDir = Join-Path $Target $SkillDir
    if (-not (Test-Path $DestSkillDir)) { New-Item -ItemType Directory -Path $DestSkillDir -Force | Out-Null }
    if (Test-Path $SrcSkillDir) {
        Get-ChildItem -Path $SrcSkillDir -Directory | ForEach-Object {
            $skillName = $_.Name
            $skillMd = Join-Path $_.FullName "SKILL.md"
            if (Test-ValidSkillMd -SkillMdPath $skillMd -SkillName $skillName) {
                Copy-ItemWithCheck -Src $_.FullName -Dest (Join-Path $DestSkillDir $skillName) -IsDir $true
            } else {
                Log-Warn "Keeping existing mirror for $skillName (source has invalid SKILL.md)"
                $script:SkillErrors++
            }
        }
    }
    Copy-ItemWithCheck -Src (Join-Path $ScriptDir $TemplateDir) -Dest (Join-Path $Target $TemplateDir) -IsDir $true
    Copy-ItemWithCheck -Src (Join-Path $ScriptDir "agents") -Dest (Join-Path $Target "agents") -IsDir $true
    Copy-ItemWithCheck -Src (Join-Path $ScriptDir "runtime") -Dest (Join-Path $Target "runtime") -IsDir $true

    # Governance assets consumed by the architecture and language gates.
    foreach ($GovernanceDir in @("contracts", "policies", "profiles")) {
        $GovernanceSource = Join-Path (Join-Path $ScriptDir ".agents") $GovernanceDir
        if (Test-Path $GovernanceSource) {
            Copy-ItemWithCheck -Src $GovernanceSource -Dest (Join-Path $Target $GovernanceDir) -IsDir $true
        }
    }
}

function Invoke-GlobalInstall {
    $target = $GlobalHomeAgents
    Log-Info "Installing shared framework payload into $target ..."
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-SharedPayload -Target $target

    # Ship the scope helper globally so re-runs and uninstall can reuse it.
    $libDest = Join-Path $target "install-lib"
    New-Item -ItemType Directory -Path $libDest -Force | Out-Null
    if (Test-Path $ScopeHelper) { Copy-Item -Path $ScopeHelper -Destination (Join-Path $libDest "aiwf_scope.py") -Force }

    # Inject the FULL managed rules block into global agent configs (idempotent).
    $script:BlockMode = "full"
    Merge-AgentsBlock -FilePath (Join-Path $target "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")
    $claudeDir = Join-Path $HOME ".claude"
    $codexDir = Join-Path $HOME ".codex"
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    New-Item -ItemType Directory -Path $codexDir -Force | Out-Null
    Merge-AgentsBlock -FilePath (Join-Path $claudeDir "CLAUDE.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")
    Merge-AgentsBlock -FilePath (Join-Path $codexDir "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")

    # Write the detection marker that puts future project installs into minimal mode.
    if ($PY -and (Test-Path $ScopeHelper)) {
        & $PY $ScopeHelper marker-write --version $Version --home $target --agents "claude,codex,antigravity"
        if ($LASTEXITCODE -eq 0) { Log-Success "Global marker written: $(Join-Path $target 'aiwf-global.json')" }
    } else {
        Log-Warn "No Python interpreter: marker not written; project installs won't auto-detect global."
    }

    # -Reclaim: slim the CURRENT project (migrate an existing full install to minimal).
    if ($Reclaim) {
        if ($PY -and (Test-Path $ScopeHelper) -and (Test-Path (Join-Path $ProjectRoot ".agents"))) {
            Log-Info "Reclaiming existing project install at $ProjectRoot into minimal mode..."
            & $PY $ScopeHelper slim-project --root $ProjectRoot --skill-dir $SkillDir --template-dir $TemplateDir |
                ForEach-Object { Log-Info "  reclaimed: $_" }
            Log-Success "Project reclaimed: duplicated payload removed, rules block downgraded to pointer."
        } else {
            Log-Warn "-Reclaim: no project .agents at $ProjectRoot (or no Python); nothing to slim."
        }
    }
    Log-Success "Global AIWF install complete at $target."
    Log-Info "New/existing projects: run '.\install.ps1' (project scope) -> minimal mode automatically."
}

# 4. Copy required files/directories
$SkillErrors = 0
if ($Scope -eq "global") {
    Invoke-GlobalInstall
    exit 0
}

# --- Scope resolution: minimal (global present) vs full project install ---
$MinimalMode = $false
if ($Scope -eq "project" -and $PY -and (Test-Path $ScopeHelper)) {
    $detectArgs = @($ScopeHelper, "detect")
    if ($AssumeGlobal) { $detectArgs += "--assume-global" }
    if ($FullInstall) { $detectArgs += "--full" }
    $detect = (& $PY @detectArgs 2>$null)
    if ($LASTEXITCODE -eq 0 -and $detect -eq "minimal") { $MinimalMode = $true }
}
if ($MinimalMode) {
    $script:BlockMode = "stub"
    Log-Info "Global AIWF install detected -> MINIMAL project mode: thin pointer only, shared payload (skills/rules/policies) skipped to avoid duplicated prompt content."
} else {
    $script:BlockMode = "full"
}

# Managed rules block: full (self-contained) or stub (pointer to global).
Merge-AgentsBlock -FilePath "AGENTS.md" -SourcePath (Join-Path $ScriptDir "AGENTS.md")
Merge-AgentsBlock -FilePath (Join-Path $InstallTarget "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")

if (-not $MinimalMode) {
    Copy-SharedPayload -Target $InstallTarget
} else {
    Log-Info "Skipped shared payload (AI_RULES.md, skills, templates, agents, runtime, contracts/policies/profiles) - provided by the global install at $GlobalHomeAgents."
}

# Deploy AIWF source-write-gate enforcement (git hooks + gate core) and wire
# git core.hooksPath so EVERY AI/editor is blocked from committing unapproved
# source changes. Idempotent and safe: missing sources are skipped.
$GateHooksSrc = Join-Path $ScriptDir "githooks"
$GateCoreSrc = Join-Path $ScriptDir "aiwf-hooks"
if (Test-Path $GateHooksSrc) {
    Copy-ItemWithCheck -Src $GateHooksSrc -Dest (Join-Path $InstallTarget "githooks") -IsDir $true
}
if (Test-Path $GateCoreSrc) {
    Copy-ItemWithCheck -Src $GateCoreSrc -Dest (Join-Path $InstallTarget "aiwf-hooks") -IsDir $true
}
# Keep the historical project-local command working as an agent-facing bridge.
# Create it only when absent so an existing project customization is preserved.
$ProjectGateBridgeDir = Join-Path $ProjectRoot "tools\aiwf-hooks"
$ProjectGateBridgeSrc = Join-Path $GateCoreSrc "aiwf_gate_bridge.py"
$ProjectGateBridge = Join-Path $ProjectGateBridgeDir "aiwf_gate.py"
if ((Test-Path $ProjectGateBridgeSrc) -and -not (Test-Path $ProjectGateBridge)) {
    New-Item -ItemType Directory -Path $ProjectGateBridgeDir -Force | Out-Null
    Copy-Item -Path $ProjectGateBridgeSrc -Destination $ProjectGateBridge -Force
    Log-Info "Created AIWF gate bridge: $ProjectGateBridge"
}
# Deploy the config-driven release orchestrator (engine + entry) next to each other.
$RelEngineSrc = Join-Path $ScriptDir "aiwf_release"
$RelEntrySrc = Join-Path $ScriptDir "release.py"
if (Test-Path $RelEngineSrc) {
    Copy-ItemWithCheck -Src $RelEngineSrc -Dest (Join-Path $InstallTarget "aiwf_release") -IsDir $true
}
if (Test-Path $RelEntrySrc) {
    Copy-ItemWithCheck -Src $RelEntrySrc -Dest (Join-Path $InstallTarget "release.py") -IsDir $false
}
if ($IsGit -and (Test-Path (Join-Path $InstallTarget "githooks"))) {
    git -C $ProjectRoot config core.hooksPath ".agents/githooks" 2>$null
    Log-Success "Source-write gate enabled (git core.hooksPath -> .agents/githooks)."
}

# Deploy the Claude Code auto-route layer (Claude-only per-prompt hooks):
# UserPromptSubmit routes every natural-language prompt through AIWF without
# requiring the user to type /aiwf; PreToolUse re-uses the source-write gate.
# Codex and Antigravity route via AGENTS.md (auto-read) + the git hard-gate.
$HookSrc = $null
foreach ($h in @($GateCoreSrc, (Join-Path $ScriptDir "tools\aiwf-hooks"))) {
    if (Test-Path $h) { $HookSrc = $h; break }
}
if ($HookSrc -and (Test-Path (Join-Path $HookSrc "aiwf_prompt_router.py"))) {
    $HookDest = Join-Path $InstallTarget "aiwf-hooks"
    New-Item -ItemType Directory -Path $HookDest -Force | Out-Null
    Copy-Item -Path (Join-Path $HookSrc "aiwf_prompt_router.py") -Destination (Join-Path $HookDest "aiwf_prompt_router.py") -Force
}
if ($HookSrc -and (Test-Path (Join-Path $HookSrc "claude-settings.template.json"))) {
    $ClaudeDir = Join-Path $ProjectRoot ".claude"
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
    $ClaudeSettings = Join-Path $ClaudeDir "settings.json"
    if (-not (Test-Path $ClaudeSettings)) {
        Copy-Item -Path (Join-Path $HookSrc "claude-settings.template.json") -Destination $ClaudeSettings -Force
        Log-Success "Claude auto-route hooks installed (.claude/settings.json). Open /hooks or restart Claude Code to activate."
    } else {
        Log-Warn "Existing .claude/settings.json kept; merge AIWF hooks from $HookSrc\claude-settings.template.json"
    }
}

Remove-InstalledTransientFiles -Root $InstallTarget
$DocsTargetDir = Join-Path $InstallTarget "docs"
if (-not (Test-Path $DocsTargetDir)) {
    New-Item -ItemType Directory -Path $DocsTargetDir -Force | Out-Null
}
$ReleaseGuideSource = Join-Path (Join-Path $ScriptDir "docs") "release-guide.md"
if (-not (Test-Path $ReleaseGuideSource)) {
    $ReleaseGuideSource = Join-Path (Join-Path (Join-Path (Join-Path $ScriptDir "docs") "features") "release-public-export") "docs\release-guide.md"
}
if (Test-Path $ReleaseGuideSource) {
    Copy-ItemWithCheck -Src $ReleaseGuideSource -Dest (Join-Path $DocsTargetDir "release-guide.md") -IsDir $false
}
else {
    Log-Warn "release-guide.md not found in source directory, skipping."
}
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

# 5. Install aiwf CLI binary
Log-Info "Installing aiwf CLI binary..."
$AiwfBinInstaller = Join-Path $ScriptDir "install-aiwf-bin.ps1"
if (Test-Path $AiwfBinInstaller) {
    try {
        & $AiwfBinInstaller -BinSrcDir (Join-Path $ScriptDir "bin")
    } catch {
        Log-Warn "aiwf binary install failed: $_ - will use PATH or embedded fallback."
    }
} else {
    Log-Warn "install-aiwf-bin.ps1 not found - ensure 'aiwf' is in PATH."
}

# 6. Validation
$MissingFiles = 0
if ($MinimalMode) {
    # Minimal mode: shared payload is global; only project-local artifacts are required.
    $RequiredFiles = @("AGENTS.md", "MANIFEST.json")
} else {
    $RequiredFiles = @("AGENTS.md", "AI_RULES.md", "MANIFEST.json", $SkillDir, $TemplateDir, "agents", "runtime", "docs/release-guide.md")
}
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

if ($SkillErrors -gt 0) {
    Log-Error "Installation completed with warnings: $SkillErrors skill(s) skipped due to invalid SKILL.md frontmatter."
    exit 1
}

# 7. Initialize workspace with aiwf CLI (uses aiwf init)
$AiwfBin = Get-Command aiwf -ErrorAction SilentlyContinue
if ($AiwfBin) {
    Log-Info "Initializing aiwf workspace..."
    $env:AIWF_WORKSPACE_ROOT = $ProjectRoot
    & aiwf init . --non-interactive --no-git --quiet 2>&1 | ForEach-Object { Log-Info $_ }
    & aiwf config --check-only --no-start 2>&1 | ForEach-Object { Log-Info $_ }
    Remove-InstalledTransientFiles -Root $InstallTarget
    $env:AIWF_WORKSPACE_ROOT = $null
} else {
    Write-Host "[WARN] aiwf CLI not found in PATH - skipping workspace initialization." -ForegroundColor Yellow
    Write-Host "[WARN] Run 'aiwf init' manually after installing the aiwf CLI." -ForegroundColor Yellow
}

Log-Success "AI Skill Framework v$VERSION has been successfully installed!"
Write-Host "--------------------------------------------------"
Write-Host "Installation Summary:"
Write-Host "  Location:  $InstallTarget/"
if ($MinimalMode) {
    Write-Host "  Mode:      MINIMAL (global install detected at $GlobalHomeAgents)"
    Write-Host "  Rules:     $(Join-Path $GlobalHomeAgents 'AI_RULES.md') (global; not duplicated per-project)"
    Write-Host "  Skills:    $(Join-Path $GlobalHomeAgents $SkillDir)/ (global)"
    Write-Host "  Project:   state/config/hooks + thin pointer block in AGENTS.md"
} else {
    Write-Host "  Mode:      FULL project install"
    Write-Host "  Rules:     $(Join-Path $InstallTarget 'AI_RULES.md')"
    Write-Host "  Skills:    $(Join-Path $InstallTarget $SkillDir)/"
    Write-Host "  Templates: $(Join-Path $InstallTarget $TemplateDir)/"
}
Write-Host "--------------------------------------------------"
Log-Info "To use these skills, make sure your AI Agent workspace points to $InstallTarget/."

# Register project in central registry so 'aiwf update -All' can find it
$RegistryDir  = Join-Path $env:LOCALAPPDATA "aiwf"
$RegistryFile = Join-Path $RegistryDir "registry.json"
if (-not (Test-Path $RegistryDir)) { New-Item -ItemType Directory -Path $RegistryDir -Force | Out-Null }
$projects = @()
if (Test-Path $RegistryFile) {
    try {
        $parsedProjects = Get-Content -Raw $RegistryFile | ConvertFrom-Json
        foreach ($projectEntry in @($parsedProjects)) {
            if ($projectEntry -is [string]) {
                foreach ($candidate in ($projectEntry -split '(?=[A-Za-z]:\\)')) {
                    if (-not [string]::IsNullOrWhiteSpace($candidate)) { $projects += $candidate.Trim() }
                }
            } elseif ($null -ne $projectEntry) {
                $projects += [string]$projectEntry
            }
        }
    } catch { $projects = @() }
    if ($null -eq $projects) { $projects = @() }
}
$entry = (Resolve-Path $ProjectRoot).Path
if ($projects -notcontains $entry) {
    $projects += $entry
    Log-Info "Project registered in AIWF registry: $entry"
} else {
    Log-Info "Project already in AIWF registry: $entry"
}
ConvertTo-Json -InputObject @($projects) -Compress | Set-Content -Path $RegistryFile -Encoding UTF8
