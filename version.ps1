# ==============================================================================
# AI Skill Framework Version Tool
# Reports active and repository version information for Windows.
# ==============================================================================

# Locate Script Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptDir)) { $ScriptDir = Get-Location }

$ManifestPath = Join-Path $ScriptDir "MANIFEST.json"
$Version = "unknown"
if (Test-Path $ManifestPath) {
    try {
        $Manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
        $Version = $Manifest.version
    }
    catch {}
}

$OS_Platform = "Windows (" + [System.Environment]::OSVersion.VersionString + ")"

Write-Host "--------------------------------------------------"
Write-Host "AI Skill Framework CLI"
Write-Host "  Framework Version:  v$Version"
Write-Host "  Repository Version: v$Version"
Write-Host "  Location:           $ScriptDir"
Write-Host "  Supported Platform: $OS_Platform"
Write-Host "--------------------------------------------------"
