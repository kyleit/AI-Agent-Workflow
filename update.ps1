<#
.SYNOPSIS
    AI Skill Framework Updater for Windows PowerShell with Release Channels support.
.DESCRIPTION
    Safely synchronizes existing installations via HTTPS Manifest or local sync without overwriting user customizations.
.PARAMETER Force
    Force synchronization even if versions match or to downgrade.
.PARAMETER All
    Update all registered projects globally.
#>

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$All,
    [switch]$Current
)

# Logging helpers
function Log-Info ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Warn ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error ($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Log-Success ($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

if ($All) {
    Log-Info "Updating all registered projects globally..."
    python3 (Join-Path $ScriptDir "skills/workflow-runtime/scripts/workflow_runtime.py") update --all
    exit 0
}

# 1. Determine Local Configuration Paths
$InstallTarget = ".agents"
$LocalManifestPath = Join-Path $InstallTarget "MANIFEST.json"
$ContextPath = Join-Path $InstallTarget "state/context.json"
$SessionPath = Join-Path $InstallTarget ".session.json"

# Default fallback values
$CurrentVersion = "0.0.0"
$ReleaseChannel = "stable"

# Read current version from target manifest if exists
if (Test-Path $LocalManifestPath) {
    try {
        $tm = Get-Content -Raw -Path $LocalManifestPath | ConvertFrom-Json
        if ($tm.version) { $CurrentVersion = $tm.version }
        if ($tm.release_channel) { $ReleaseChannel = $tm.release_channel }
    } catch {}
}

# Check release_channel in context.json
if (Test-Path $ContextPath) {
    try {
        $ctx = Get-Content -Raw -Path $ContextPath | ConvertFrom-Json
        if ($ctx.release_channel) { $ReleaseChannel = $ctx.release_channel }
    } catch {}
}

# Check release_channel in .session.json
if (Test-Path $SessionPath) {
    try {
        $s = Get-Content -Raw -Path $SessionPath | ConvertFrom-Json
        if ($s.release_channel) { $ReleaseChannel = $s.release_channel }
    } catch {}
}

# Normalize and validate release channel
if ($ReleaseChannel -notin @("stable", "beta", "alpha")) {
    Log-Warn "Invalid release channel value '$ReleaseChannel'. Defaulting to 'stable'."
    $ReleaseChannel = "stable"
}

Log-Info "Detected Installed Version: v$CurrentVersion"
Log-Info "Release Channel: $ReleaseChannel"

# Robust SemVer Comparator
function Compare-SemVer ($v1, $v2) {
    # Normalize by stripping 'v' prefixes
    $v1 = ($v1 -replace '^v', '').Trim()
    $v2 = ($v2 -replace '^v', '').Trim()
    
    if ($v1 -eq $v2) { return 0 }
    
    # Split into main version and prerelease tag
    $parts1 = $v1 -split '-', 2
    $parts2 = $v2 -split '-', 2
    
    $main1 = $parts1[0] -split '\.'
    $main2 = $parts2[0] -split '\.'
    
    # Pad major, minor, patch with 0 if missing
    for ($i = 0; $i -lt 3; $i++) {
        $num1 = if ($main1[$i]) { [int]$main1[$i] } else { 0 }
        $num2 = if ($main2[$i]) { [int]$main2[$i] } else { 0 }
        if ($num1 -gt $num2) { return 1 }
        if ($num1 -lt $num2) { return -1 }
    }
    
    # Compare prerelease tags
    $pre1 = if ($parts1.Length -gt 1) { $parts1[1] } else { $null }
    $pre2 = if ($parts2.Length -gt 1) { $parts2[1] } else { $null }
    
    if ($null -eq $pre1 -and $null -ne $pre2) { return 1 } # Stable > Prerelease
    if ($null -ne $pre1 -and $null -eq $pre2) { return -1 } # Prerelease < Stable
    if ($null -eq $pre1 -and $null -eq $pre2) { return 0 }
    
    # Compare prerelease tags (e.g. beta.1 vs alpha.5)
    $preParts1 = $pre1 -split '\.'
    $preParts2 = $pre2 -split '\.'
    $maxLen = [Math]::Max($preParts1.Length, $preParts2.Length)
    
    for ($i = 0; $i -lt $maxLen; $i++) {
        $p1 = if ($i -lt $preParts1.Length) { $preParts1[$i] } else { $null }
        $p2 = if ($i -lt $preParts2.Length) { $preParts2[$i] } else { $null }
        
        if ($null -eq $p1) { return -1 }
        if ($null -eq $p2) { return 1 }
        
        $isNum1 = $p1 -match '^\d+$'
        $isNum2 = $p2 -match '^\d+$'
        
        if ($isNum1 -and $isNum2) {
            $n1 = [int]$p1
            $n2 = [int]$p2
            if ($n1 -gt $n2) { return 1 }
            if ($n1 -lt $n2) { return -1 }
        } else {
            $cmp = [string]::Compare($p1, $p2, $true)
            if ($cmp -gt 0) { return 1 }
            if ($cmp -lt 0) { return -1 }
        }
    }
    return 0
}

# Helper for local sync mode (original behavior)
function Run-LocalSync {
    Log-Info "Running Local Sync Mode..."
    $ManifestPath = Join-Path $ScriptDir "MANIFEST.json"
    if (-not (Test-Path $ManifestPath)) {
        Log-Error "MANIFEST.json not found in source directory ($ScriptDir)."
        exit 1
    }
    try {
        $SrcManifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
        $SrcVersion = $SrcManifest.version
    } catch {
        Log-Error "Failed to parse root MANIFEST.json. Details: $_"
        exit 1
    }
    
    Log-Info "Available Repository Version: v$SrcVersion"
    
    $VerCompare = Compare-SemVer $SrcVersion $CurrentVersion
    if ($VerCompare -eq 0 -and -not $Force) {
        Log-Success "AI Skill Framework is already up to date (v$CurrentVersion)."
        exit 0
    }
    if ($VerCompare -lt 0 -and -not $Force) {
        Log-Error "Repository version ($SrcVersion) is older than installed version ($CurrentVersion). Use -Force to downgrade."
        exit 1
    }
    
    # Safe copy updates
    function Update-ItemWithCheck ($src, $dest) {
        if (-not (Test-Path $dest)) {
            Log-Info "Creating: $dest"
            Copy-Item -Path $src -Destination $dest -Recurse -Force | Out-Null
        } else {
            Log-Info "Updating: $dest"
            Remove-Item -Path $dest -Recurse -Force | Out-Null
            Copy-Item -Path $src -Destination $dest -Recurse -Force | Out-Null
        }
    }
    
    # Merge rules in AGENTS.md
    $srcAgents = Join-Path $ScriptDir "AGENTS.md"
    $destAgents = Join-Path $InstallTarget "AGENTS.md"
    if (Test-Path $srcAgents) {
        if (-not (Test-Path $destAgents)) {
            Copy-Item -Path $srcAgents -Destination $destAgents -Force | Out-Null
        }
    }
    
    Update-ItemWithCheck -src (Join-Path $ScriptDir "AI_RULES.md") -dest (Join-Path $InstallTarget "AI_RULES.md")
    Update-ItemWithCheck -src (Join-Path $ScriptDir "SKILLS.md") -dest (Join-Path $InstallTarget "SKILLS.md")
    Update-ItemWithCheck -src (Join-Path $ScriptDir "agents") -dest (Join-Path $InstallTarget "agents")
    Update-ItemWithCheck -src (Join-Path $ScriptDir "runtime") -dest (Join-Path $InstallTarget "runtime")
    
    $DocsTargetDir = Join-Path $InstallTarget "docs"
    if (-not (Test-Path $DocsTargetDir)) { New-Item -ItemType Directory -Path $DocsTargetDir -Force | Out-Null }
    Update-ItemWithCheck -src (Join-Path (Join-Path $ScriptDir "docs") "release-guide.md") -dest (Join-Path $DocsTargetDir "release-guide.md")
    
    # Sync skills
    $SkillDir = $SrcManifest.skill_directory
    $SrcSkills = @()
    foreach ($s in $SrcManifest.skills) { $SrcSkills += if ($s.name) { $s.name } else { $s } }
    foreach ($Skill in $SrcSkills) {
        Update-ItemWithCheck -src (Join-Path (Join-Path $ScriptDir $SkillDir) $Skill) -dest (Join-Path (Join-Path $InstallTarget $SkillDir) $Skill)
    }
    
    # Sync templates
    $TemplateDir = $SrcManifest.template_directory
    if (Test-Path (Join-Path $ScriptDir $TemplateDir)) {
        if (-not (Test-Path (Join-Path $InstallTarget $TemplateDir))) {
            New-Item -ItemType Directory -Path (Join-Path $InstallTarget $TemplateDir) -Force | Out-Null
        }
        Copy-Item -Path (Join-Path (Join-Path $ScriptDir $TemplateDir) "*") -Destination (Join-Path $InstallTarget $TemplateDir) -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
    }
    
    # Update local manifest and write version/channel
    $SrcManifest.release_channel = $ReleaseChannel
    $SrcManifest | ConvertTo-Json -Depth 10 | Out-File -FilePath $LocalManifestPath -Encoding utf8 -Force
    
    Log-Success "AI Skill Framework has been successfully updated locally to v$SrcVersion!"
}

# 2. HTTPS Update Mode
$BaseUrl = "https://raw.githubusercontent.com/kyleit/AI-Agent-Workflow/main"
$ManifestUrl = "$BaseUrl/releases/manifest.json"
if ($ReleaseChannel -eq "beta") {
    $ManifestUrl = "$BaseUrl/releases/manifest-beta.json"
} elseif ($ReleaseChannel -eq "alpha") {
    $ManifestUrl = "$BaseUrl/releases/manifest-alpha.json"
}

Log-Info "Fetching online manifest from $ManifestUrl..."
$OnlineManifest = $null
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $OnlineManifest = Invoke-RestMethod -Uri $ManifestUrl -TimeoutSec 10
} catch {
    Log-Warn "Failed to connect to the update server. Details: $_"
    # Fallback to local sync if manifest exists at root
    if (Test-Path (Join-Path $ScriptDir "MANIFEST.json")) {
        Run-LocalSync
        exit 0
    } else {
        Log-Error "Offline and no local repository source found. Cannot update."
        exit 1
    }
}

# Determine target version from online manifest
$TargetVersion = $null
$DownloadUrl = $null
$ExpectedHash = $null

if ($ReleaseChannel -eq "stable") {
    $TargetVersion = $OnlineManifest.latest_stable
} elseif ($ReleaseChannel -eq "beta") {
    $TargetVersion = $OnlineManifest.latest_beta
} elseif ($ReleaseChannel -eq "alpha") {
    $TargetVersion = $OnlineManifest.latest_alpha
}

# Traversal / manual parse fallback if latest_xxx fields are not resolved
if ($null -eq $TargetVersion -or $null -eq $OnlineManifest.releases) {
    # Sort releases and pick top matching channel
    $MatchedReleases = @()
    foreach ($r in $OnlineManifest.releases) {
        $c = $r.channel
        $isOk = $false
        if ($ReleaseChannel -eq "alpha") {
            $isOk = $true
        } elseif ($ReleaseChannel -eq "beta") {
            if ($c -eq "stable" -or $c -eq "beta" -or $r.version -match "-rc\.") {
                $isOk = $true
            }
        } else {
            if ($c -eq "stable") {
                $isOk = $true
            }
        }
        if ($isOk) { $MatchedReleases += $r }
    }
    
    if ($MatchedReleases.Count -gt 0) {
        $MaxRelease = $MatchedReleases[0]
        foreach ($r in $MatchedReleases) {
            if ((Compare-SemVer $r.version $MaxRelease.version) -gt 0) {
                $MaxRelease = $r
            }
        }
        $TargetVersion = $MaxRelease.version
        $DownloadUrl = $MaxRelease.download_url
        $ExpectedHash = $MaxRelease.sha256
    }
} else {
    foreach ($r in $OnlineManifest.releases) {
        if ($r.version -eq $TargetVersion) {
            $DownloadUrl = $r.download_url
            $ExpectedHash = $r.sha256
            break
        }
    }
}

if ($null -eq $TargetVersion -or $null -eq $DownloadUrl) {
    Log-Error "Could not find a valid release version for channel '$ReleaseChannel' in manifest."
    exit 1
}

Log-Info "Available Online Version: v$TargetVersion"

# Compare version tags
$VerCompare = Compare-SemVer $TargetVersion $CurrentVersion
if ($VerCompare -eq 0 -and -not $Force) {
    Log-Success "AI Skill Framework is already up to date (v$CurrentVersion)."
    exit 0
}
if ($VerCompare -lt 0 -and -not $Force) {
    Log-Error "Remote version ($TargetVersion) is older than current version ($CurrentVersion). Downgrade blocked. Use -Force to downgrade."
    exit 1
}

# Download ZIP package
Log-Info "Downloading release v$TargetVersion from $DownloadUrl..."
$TempZip = Join-Path $env:TEMP "ai-agent-workflow-update.zip"
if (Test-Path $TempZip) { Remove-Item $TempZip -Force }

try {
    $WebClient = New-Object System.Net.WebClient
    $WebClient.DownloadFile($DownloadUrl, $TempZip)
} catch {
    Log-Error "Failed to download ZIP package. Details: $_"
    exit 1
}

# Verify SHA256 Checksum
Log-Info "Verifying checksum..."
$FileHash = (Get-FileHash -Path $TempZip -Algorithm SHA256).Hash.ToLower()
$CleanExpectedHash = $ExpectedHash.Trim().ToLower()

if ($FileHash -ne $CleanExpectedHash) {
    Log-Error "Checksum verification failed!"
    Log-Error "Expected SHA256: $CleanExpectedHash"
    Log-Error "Actual SHA256:   $FileHash"
    if (Test-Path $TempZip) { Remove-Item $TempZip -Force }
    exit 1
}
Log-Success "Checksum verified successfully."

# Backup configs
Log-Info "Backing up local configurations..."
$BackupTempDir = Join-Path $ScriptDir ".agents_backup_temp"
if (Test-Path $BackupTempDir) { Remove-Item $BackupTempDir -Recurse -Force }
New-Item -ItemType Directory -Path $BackupTempDir -Force | Out-Null

$FilesToBackup = @(
    ".session.json",
    "state",
    "config",
    "memory.config.json",
    "obsidian.config.json",
    "project.config.json",
    "workflow.config.json",
    "release.config.json"
)

foreach ($item in $FilesToBackup) {
    $srcPath = Join-Path $InstallTarget $item
    if (Test-Path $srcPath) {
        $destPath = Join-Path $BackupTempDir $item
        Copy-Item -Path $srcPath -Destination $destPath -Recurse -Force | Out-Null
    }
}

# Safe extraction
Log-Info "Extracting update package..."
try {
    if (Test-Path $InstallTarget) {
        Get-ChildItem -Path $InstallTarget -Force | ForEach-Object {
            Remove-Item $_.FullName -Recurse -Force | Out-Null
        }
    } else {
        New-Item -ItemType Directory -Path $InstallTarget -Force | Out-Null
    }
    
    Expand-Archive -Path $TempZip -DestinationPath $InstallTarget -Force
    
    # Check for single nested folder inside target
    $ExtractedItems = Get-ChildItem -Path $InstallTarget
    if ($ExtractedItems.Count -eq 1 -and $ExtractedItems[0].PSIsContainer) {
        $NestedFolder = $ExtractedItems[0].FullName
        Log-Info "Unpacking nested folder: $($ExtractedItems[0].Name)"
        Get-ChildItem -Path $NestedFolder | ForEach-Object {
            Move-Item -Path $_.FullName -Destination $InstallTarget -Force
        }
        Remove-Item -Path $NestedFolder -Recurse -Force
    }
} catch {
    Log-Error "Failed to extract ZIP update. Reverting changes..."
    if (Test-Path $BackupTempDir) {
        if (-not (Test-Path $InstallTarget)) { New-Item -ItemType Directory -Path $InstallTarget -Force | Out-Null }
        Get-ChildItem -Path $BackupTempDir | Copy-Item -Destination $InstallTarget -Recurse -Force | Out-Null
        Log-Info "Rollback completed. Original configuration restored."
    }
    if (Test-Path $TempZip) { Remove-Item $TempZip -Force }
    if (Test-Path $BackupTempDir) { Remove-Item $BackupTempDir -Recurse -Force }
    exit 1
}

# Restore configurations
Log-Info "Restoring configurations..."
if (Test-Path $BackupTempDir) {
    Get-ChildItem -Path $BackupTempDir | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $InstallTarget -Recurse -Force | Out-Null
    }
    Remove-Item $BackupTempDir -Recurse -Force
}

# Update local Manifest with target version and channel
if (Test-Path $LocalManifestPath) {
    try {
        $m = Get-Content -Raw -Path $LocalManifestPath | ConvertFrom-Json
        $m.version = $TargetVersion
        $m.release_channel = $ReleaseChannel
        $m | ConvertTo-Json -Depth 10 | Out-File -FilePath $LocalManifestPath -Encoding utf8 -Force
    } catch {
        Log-Warn "Failed to update Target version in MANIFEST.json. Details: $_"
    }
}

if (Test-Path $TempZip) { Remove-Item $TempZip -Force }
Log-Success "AI Skill Framework has been successfully updated online to v$TargetVersion!"
Write-Host "--------------------------------------------------"
Log-Info "Run aiwf doctor to confirm workspace integrity."
