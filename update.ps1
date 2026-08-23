<#
.SYNOPSIS
    AI Skill Framework Updater for Windows PowerShell.
.DESCRIPTION
    Safely synchronizes existing installations without overwriting user customizations.
.PARAMETER Force
    Force synchronization even if versions match.
.PARAMETER All
    Update all registered projects (delegated to aiwf CLI).
.PARAMETER Current
    Update only the current project.
#>

param(
    [switch]$Force,
    [switch]$All,
    [switch]$Current,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Remaining
)

# Normalize Linux-style double-dash flags (--all, --force, --current)
# PowerShell binds -Flag but not --flag (Linux style), so we check $Remaining.
foreach ($a in $Remaining) {
    switch ($a.ToLower()) {
        "--all"     { $All     = $true }
        "--force"   { $Force   = $true }
        "--current" { $Current = $true }
    }
}


# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Error "[ERROR] $msg" }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

if ($All) {
    $RegistryFile = Join-Path $env:LOCALAPPDATA "aiwf\registry.json"
    $found = @()

    # 1. Read from central registry (written by 'aiwf install')
    if (Test-Path $RegistryFile) {
        try {
            $reg = Get-Content -Raw $RegistryFile | ConvertFrom-Json
            if ($reg) { $found = @($reg) | Where-Object { Test-Path (Join-Path $_ ".agents\MANIFEST.json") } }
        } catch {}
    }

    # 2. Fallback: filesystem scan if registry is empty
    if ($found.Count -eq 0) {
        Log-Info "Registry empty or not found. Scanning drives for AIWF-managed projects..."
        $searchRoots = [System.Collections.Generic.List[string]]::new()
        foreach ($sub in @("", "source", "projects", "dev", "repos", "workspace", "code", "work", "git")) {
            $p = if ($sub) { Join-Path $env:USERPROFILE $sub } else { $env:USERPROFILE }
            if (Test-Path $p) { $searchRoots.Add($p) }
        }
        $drives = [System.IO.DriveInfo]::GetDrives() |
            Where-Object { $_.DriveType -in @("Fixed","Network","Ram") -and $_.IsReady }
        foreach ($drive in $drives) {
            # Add drive root itself (catches projects like A:\myproject)
            if ($searchRoots -notcontains $drive.Name.TrimEnd('\')) { $searchRoots.Add($drive.Name.TrimEnd('\')) }
            foreach ($sub in @("dev","src","projects","repos","code","work","Users")) {
                $p = Join-Path $drive.Name $sub
                if ((Test-Path $p) -and $searchRoots -notcontains $p) { $searchRoots.Add($p) }
            }
        }
        foreach ($root in $searchRoots) {
            Get-ChildItem $root -Recurse -Depth 6 -Filter "MANIFEST.json" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DirectoryName -like "*\.agents" -and
                $_.FullName -notlike "*\.aiwf\framework-source*" -and
                $_.FullName -notlike "*\node_modules\*" -and
                $_.FullName -notlike "*\scratch\*" -and
                $_.FullName -notlike "*\.import_linter_cache\*" -and
                $_.FullName -notlike "*\.ruff_cache\*" -and
                $_.FullName -notlike "*\.git\*"
            } | ForEach-Object {
                $projectDir = (Resolve-Path (Split-Path -Parent $_.DirectoryName)).Path
                if ($found -notcontains $projectDir) { $found += $projectDir }
            }
        }
    }

    if ($found.Count -eq 0) {
        Log-Warn "No AIWF-managed projects found."
        Log-Warn "Run 'aiwf install' inside a project directory to register it."
        exit 0
    }

    Log-Info "Found $($found.Count) registered project(s):"
    $found | ForEach-Object { Write-Host "  - $_" }
    Write-Host ""

    $ok = 0; $fail = 0
    foreach ($proj in $found) {
        if (-not (Test-Path $proj)) {
            Log-Warn "Skipping (path not found): $proj"
            $fail++; continue
        }
        Log-Info "Updating: $proj"
        Push-Location $proj
        try {
            & $MyInvocation.MyCommand.Path $(if ($Force) { "-Force" })
            if ($LASTEXITCODE -eq 0) { $ok++ } else { $fail++ }
        } finally {
            Pop-Location
        }
    }

    Write-Host ""
    Log-Success "Update-All complete. Success: $ok  Skipped/Failed: $fail"
    exit 0
}

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
}

$ResolvedProjectRoot = (Resolve-Path (Get-Location)).Path
$ResolvedScriptDir = (Resolve-Path $ScriptDir).Path
if ($ResolvedProjectRoot -eq $ResolvedScriptDir) {
    Log-Success "Target is the framework source repository itself. Skipping update."
    exit 0
}

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
    if (-not (Test-Path $src)) {
        Log-Warn "Source path not found in framework root, skipping: $src"
        return
    }
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
    
    # Resolve to absolute paths using PowerShell provider (NOT .NET CWD)
    # This avoids the well-known PowerShell/.NET current-directory mismatch
    $SourcePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SourcePath)
    $FilePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($FilePath)

    $SrcContent = [System.IO.File]::ReadAllText($SourcePath, [System.Text.Encoding]::UTF8)
    $BeginMarker = "<!-- AIWF:RULES:BEGIN -->"
    $EndMarker = "<!-- AIWF:RULES:END -->"
    
    $EscBegin = [Regex]::Escape($BeginMarker)
    $EscEnd = [Regex]::Escape($EndMarker)
    $Regex = "(?s)" + $EscBegin + ".*?" + $EscEnd
    
    $Match = [Regex]::Match($SrcContent, $Regex)
    if ($Match.Success) {
        $BlockContent = $Match.Value
    } else {
        $BlockContent = $SrcContent
    }

    if (-not (Test-Path $FilePath)) {
        $ParentDir = Split-Path -Parent $FilePath
        if ($ParentDir -and -not (Test-Path $ParentDir)) {
            New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
        }
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
if (-not (Test-Path $InstallTarget)) {
    New-Item -ItemType Directory -Force -Path $InstallTarget | Out-Null
}
Merge-AgentsBlock -FilePath (Join-Path $InstallTarget "AGENTS.md") -SourcePath (Join-Path $ScriptDir "AGENTS.md")
Update-ItemWithCheck -src (Join-Path $ScriptDir "AI_RULES.md") -dest (Join-Path $InstallTarget "AI_RULES.md")
Update-ItemWithCheck -src (Join-Path $ScriptDir "SKILLS.md") -dest (Join-Path $InstallTarget "SKILLS.md")
Update-ItemWithCheck -src (Join-Path $ScriptDir "agents") -dest (Join-Path $InstallTarget "agents")
Update-ItemWithCheck -src (Join-Path $ScriptDir "runtime") -dest (Join-Path $InstallTarget "runtime")

# Refresh AIWF source-write-gate enforcement (git hooks + gate core) and ensure
# git core.hooksPath is wired. Keeps every AI/editor blocked from committing
# unapproved source changes across updates.
$GateHooksSrc = Join-Path $ScriptDir "githooks"
$GateCoreSrc = Join-Path $ScriptDir "aiwf-hooks"
if (Test-Path $GateHooksSrc) {
    Update-ItemWithCheck -src $GateHooksSrc -dest (Join-Path $InstallTarget "githooks")
}
if (Test-Path $GateCoreSrc) {
    Update-ItemWithCheck -src $GateCoreSrc -dest (Join-Path $InstallTarget "aiwf-hooks")
}
# Refresh the config-driven release orchestrator (engine + entry).
$RelEngineSrc = Join-Path $ScriptDir "aiwf_release"
$RelEntrySrc = Join-Path $ScriptDir "release.py"
if (Test-Path $RelEngineSrc) {
    Update-ItemWithCheck -src $RelEngineSrc -dest (Join-Path $InstallTarget "aiwf_release")
}
if (Test-Path $RelEntrySrc) {
    Update-ItemWithCheck -src $RelEntrySrc -dest (Join-Path $InstallTarget "release.py")
}
if ($IsGit -and (Test-Path (Join-Path $InstallTarget "githooks"))) {
    git -C $ProjectRoot config core.hooksPath ".agents/githooks" 2>$null
    Log-Success "Source-write gate wired (git core.hooksPath -> .agents/githooks)."
}
$DocsTargetDir = Join-Path $InstallTarget "docs"
if (-not (Test-Path $DocsTargetDir)) {
    New-Item -ItemType Directory -Path $DocsTargetDir -Force | Out-Null
}
Update-ItemWithCheck -src (Join-Path (Join-Path $ScriptDir "docs") "release-guide.md") -dest (Join-Path $DocsTargetDir "release-guide.md")
Update-ItemWithCheck -src $ManifestPath -dest $TargetManifestPath

# Ensure .gitignore exists in target and ignores logs
function Ensure-GitIgnore ($targetDir) {
    $GitIgnorePath = Join-Path $targetDir ".gitignore"
    $DefaultContent = @(
        ".session.json",
        "state/",
        "runtime/*.db",
        "runtime/*.db-journal",
        "runtime/*.db-wal",
        "runtime/env_cache.json",
        "runtime/logs/"
    )

    if (-not (Test-Path $GitIgnorePath)) {
        Log-Info "Creating: $GitIgnorePath"
        $DefaultContent | Out-File -FilePath $GitIgnorePath -Encoding utf8 -Force
    } else {
        $Lines = Get-Content -Path $GitIgnorePath
        $HasLogsPattern = $false
        foreach ($Line in $Lines) {
            $t = $Line.Trim()
            if ($t -eq "runtime/logs/" -or $t -eq "runtime/logs") {
                $HasLogsPattern = $true
                break
            }
        }
        if (-not $HasLogsPattern) {
            Log-Info "Adding runtime/logs/ to $GitIgnorePath"
            Add-Content -Path $GitIgnorePath -Value "`r`nruntime/logs/" -Force
        }
    }
}
Ensure-GitIgnore -targetDir $InstallTarget

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

# Copy active skills
$SkillErrors = 0
foreach ($Skill in $SrcSkills) {
    $srcSkillPath = Join-Path (Join-Path $ScriptDir $SkillDir) $Skill
    $skillMdPath = Join-Path $srcSkillPath "SKILL.md"
    if (Test-ValidSkillMd -SkillMdPath $skillMdPath -SkillName $Skill) {
        Update-ItemWithCheck -src $srcSkillPath -dest (Join-Path (Join-Path $InstallTarget $SkillDir) $Skill)
    } else {
        Log-Warn "Keeping existing mirror for $Skill (source has invalid SKILL.md)"
        $SkillErrors++
    }
}

# Copy templates
if (Test-Path (Join-Path $ScriptDir $TemplateDir)) {
    if (-not (Test-Path (Join-Path $InstallTarget $TemplateDir))) {
        New-Item -ItemType Directory -Path (Join-Path $InstallTarget $TemplateDir) -Force | Out-Null
    }
    Copy-Item -Path (Join-Path (Join-Path $ScriptDir $TemplateDir) "*") -Destination (Join-Path $InstallTarget $TemplateDir) -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
}

if ($SkillErrors -gt 0) {
    Log-Error "Update completed with warnings: $SkillErrors skill(s) skipped due to invalid SKILL.md frontmatter."
    exit 1
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
