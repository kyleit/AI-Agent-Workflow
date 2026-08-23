# One-command entry to the msgbus-ws client (Windows).
# Auto-loads the saved profile at ~/.aiwf/msgbus.json (set once via `init`).
#
#   aiwf-msgbus init --host msgbus.example.invalid --tls --token <TOKEN>
#   aiwf-msgbus join
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $here "..\scripts\msgbus_client.py") @args
exit $LASTEXITCODE
