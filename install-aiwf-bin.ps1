# ==============================================================================
# install-aiwf-bin.ps1 — Install or update the aiwf CLI binary (Windows PowerShell)
#
# Detects the current architecture, copies the matching prebuilt binary from
# the framework's bin\ directory to %USERPROFILE%\.aiwf\bin\, and adds it to
# the user's PATH if not already present.
#
# Called automatically by install.ps1 and update.ps1.
# Can also be run standalone:
#   .\install-aiwf-bin.ps1 [-BinSrcDir "path\to\bin"] [-BinDestDir "path\to\dest"]
# ==============================================================================

param(
    [string]$BinSrcDir  = "",
    [string]$BinDestDir = ""
)

function Log-Info    { param($msg) Write-Host "[INFO]    $msg" -ForegroundColor Cyan }
function Log-Warn    { param($msg) Write-Host "[WARN]    $msg" -ForegroundColor Yellow }
function Log-Error   { param($msg) Write-Host "[ERROR]   $msg" -ForegroundColor Red }
function Log-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }

# ── Detect architecture ───────────────────────────────────────────────────────
$arch = $env:PROCESSOR_ARCHITECTURE
switch ($arch) {
    "AMD64"  { $GoArch = "amd64" }
    "ARM64"  { $GoArch = "arm64" }
    default  {
        Log-Warn "Unsupported architecture: $arch — defaulting to amd64"
        $GoArch = "amd64"
    }
}
$PlatformBin = "aiwf_windows_${GoArch}.exe"

# ── Resolve paths ─────────────────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($BinSrcDir)) {
    $BinSrcDir = Join-Path $ScriptDir "bin"
}
if ([string]::IsNullOrEmpty($BinDestDir)) {
    $BinDestDir = Join-Path $env:USERPROFILE ".aiwf\bin"
}

$SrcFile  = Join-Path $BinSrcDir $PlatformBin
$DestFile = Join-Path $BinDestDir "aiwf.exe"

Log-Info "aiwf binary: $PlatformBin"
Log-Info "Source:      $SrcFile"
Log-Info "Destination: $DestFile"

# ── Validate source binary ─────────────────────────────────────────────────────
if (-not (Test-Path $SrcFile)) {
    Log-Warn "aiwf binary not found at $SrcFile — skipping binary install."
    Log-Warn "The framework will fall back to PATH resolution or manual install."
    exit 0
}

$FileSize = (Get-Item $SrcFile).Length
if ($FileSize -lt 32) {
    Log-Warn "aiwf binary at $SrcFile appears to be a stub ($FileSize bytes) — skipping."
    exit 0
}

# ── Install binary ────────────────────────────────────────────────────────────
if (-not (Test-Path $BinDestDir)) {
    New-Item -ItemType Directory -Path $BinDestDir -Force | Out-Null
}

Copy-Item -Path $SrcFile -Destination $DestFile -Force
Log-Success "aiwf binary installed: $DestFile"

# ── Add to User PATH if missing ───────────────────────────────────────────────
$UserPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDestDir*") {
    $NewPath = "$UserPath;$BinDestDir"
    [System.Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Log-Success "Added $BinDestDir to user PATH (restart terminal to take effect)"
} else {
    Log-Info "$BinDestDir already in user PATH"
}
