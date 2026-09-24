# Portable launcher for the AIWF multi-agent-loop orchestrator (PowerShell / pwsh).
# Resolves python -> python3 -> py -3 (>= 3.9); on failure emits an envelope and
# points to PROTOCOL.md. Canonical entrypoint remains `aiwf orchestrate`.
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
            & $c.Exe @($c.Args) -m malo @args
            exit $LASTEXITCODE
        }
    }
}

[Console]::Error.WriteLine('{"error":"NoPythonInterpreter","message":"No python (>=3.9) found. Follow PROTOCOL.md.","fallback":"PROTOCOL.md"}')
exit 3
