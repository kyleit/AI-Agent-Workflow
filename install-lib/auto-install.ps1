<# Registers or executes the framework clone's global-install Git hooks. #>
[CmdletBinding()]
param([switch]$Register)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $PSScriptRoot

if ($Register) {
    if (-not (Test-Path -LiteralPath (Join-Path $SourceRoot ".git"))) {
        Write-Warning "Auto-install hook skipped: the framework package is not a Git repository root."
        exit 0
    }
    $gitRoot = & git -C $SourceRoot rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $gitRoot -or
        [IO.Path]::GetFullPath($gitRoot.Trim()) -ne [IO.Path]::GetFullPath($SourceRoot)) {
        Write-Warning "Auto-install hook skipped: the framework package is not a Git repository root."
        exit 0
    }
    $hookDir = & git -C $SourceRoot rev-parse --path-format=absolute --git-path hooks
    if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git hook directory." }
    $hookDir = $hookDir.Trim()
    New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
    $block = @'
# AIWF:AUTO-INSTALL:BEGIN
if [ "$(git config --bool aiwf.autoInstall 2>/dev/null)" != "false" ]; then
    aiwf_root=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -n "$aiwf_root" ] && [ -f "$aiwf_root/install-lib/auto-install.ps1" ]; then
        if command -v powershell.exe >/dev/null 2>&1; then
            powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$aiwf_root/install-lib/auto-install.ps1" </dev/null || exit $?
        elif command -v pwsh >/dev/null 2>&1; then
            pwsh -NoProfile -File "$aiwf_root/install-lib/auto-install.ps1" </dev/null || exit $?
        else
            echo "AIWF: pull completed, but auto-install requires PowerShell. Run install.ps1 -Scope global -Force manually." >&2
            exit 1
        fi
    fi
fi
# AIWF:AUTO-INSTALL:END
'@
    foreach ($hook in @("post-merge", "post-rewrite")) {
        $hookPath = Join-Path $hookDir $hook
        $content = "#!/bin/sh`n"
        if (Test-Path -LiteralPath $hookPath) {
            $content = [IO.File]::ReadAllText($hookPath)
            if ($content.StartsWith("#!") -and $content -notmatch '\A#![^\r\n]*\b(?:ba|da|z|k)?sh\b') {
                Write-Warning "Auto-install skipped for non-shell hook: $hookPath"
                continue
            }
            $content = [regex]::Replace($content, '(?ms)^# AIWF:AUTO-INSTALL:BEGIN\r?\n.*?^# AIWF:AUTO-INSTALL:END\r?\n?', '')
        }
        if ($content.StartsWith("#!")) {
            $newline = $content.IndexOf("`n")
            if ($newline -lt 0) { $content += "`n"; $newline = $content.Length - 1 }
            $content = $content.Substring(0, $newline + 1) + $block + "`n" + $content.Substring($newline + 1)
        } else {
            $content = "#!/bin/sh`n" + $block + "`n" + $content
        }
        # Git shell hooks require LF and UTF-8 without BOM, including on Windows.
        [IO.File]::WriteAllText($hookPath, $content.Replace("`r`n", "`n"), (New-Object Text.UTF8Encoding($false)))
        Write-Host "[INFO] Automatic global installation registered: $hookPath"
    }
    exit 0
}

Write-Host "[INFO] Git update completed. Applying AIWF global installation..."
$powershellExe = (Get-Process -Id $PID).Path
& $powershellExe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SourceRoot "install.ps1") -Scope global -Force
if ($LASTEXITCODE -ne 0) {
    Write-Error "Git update completed, but AIWF global installation failed. Retry install.ps1 -Scope global -Force."
    exit 1
}
exit 0
