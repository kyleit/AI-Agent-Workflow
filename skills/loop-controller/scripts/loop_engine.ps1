# Portable launcher for the AIWF loop engine (Windows PowerShell / pwsh).
#
# Resolves a Python >= 3.9 interpreter exposed as `python`, `python3`, or the
# Windows launcher `py -3`. If none is found it emits a machine-readable
# envelope instructing the agent to fall back to PROTOCOL.md (hand-execution).
#
# Canonical agent-facing entrypoint remains `aiwf loop <...>`; this launcher is
# the raw-script fallback for environments without the installed `aiwf` CLI.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = $dir

$verCheck = 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'
$candidates = @(
    @{ Exe = 'python3'; Args = @() },
    @{ Exe = 'python';  Args = @() },
    @{ Exe = 'py';      Args = @('-3') }
)

foreach ($c in $candidates) {
    if (Get-Command $c.Exe -ErrorAction SilentlyContinue) {
        & $c.Exe @($c.Args) -c $verCheck 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $c.Exe @($c.Args) -m loop_engine @args
            exit $LASTEXITCODE
        }
    }
}

[Console]::Error.WriteLine('{"error":"NoPythonInterpreter","message":"No python (>=3.9) found. Follow PROTOCOL.md to run the loop controller by hand.","fallback":"PROTOCOL.md"}')
exit 3
