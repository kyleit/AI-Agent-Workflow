@echo off
REM ==============================================================================
REM AI Skill Framework Global Bootstrap Installer (Windows CMD Batch)
REM Runs the PowerShell bootstrap and installs the CMD global wrapper.
REM ==============================================================================

echo [INFO] Invoking PowerShell bootstrap...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell bootstrap failed.
    exit /b %ERRORLEVEL%
)

REM Create CMD CLI wrapper so users can type 'aiwf' in Command Prompt
set "BIN_DIR=%LOCALAPPDATA%\aiwf\bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

set "CLI_BAT=%BIN_DIR%\aiwf.bat"
echo [INFO] Creating CMD CLI wrapper at: %CLI_BAT%

(
echo @echo off
echo powershell -NoProfile -ExecutionPolicy Bypass -File "%BIN_DIR%\aiwf.ps1" %%*
) > "%CLI_BAT%"

echo [SUCCESS] Global CMD wrapper installed!
echo [INFO] Please restart your Command Prompt or terminal to reload PATH.
