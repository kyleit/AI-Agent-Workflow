#!/bin/sh
# Portable launcher for the AIWF multi-agent-loop orchestrator (POSIX sh).
# Resolves python3 -> python -> py -3 (>= 3.9); on failure prints an envelope
# and points to PROTOCOL.md. Canonical entrypoint remains `aiwf orchestrate`.
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

PY=""
for cand in python3 python "py -3"; do
    # shellcheck disable=SC2086
    if $cand -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done

if [ -z "$PY" ]; then
    printf '%s\n' '{"error":"NoPythonInterpreter","message":"No python3/python/py (>=3.9) found. Follow PROTOCOL.md.","fallback":"PROTOCOL.md"}' >&2
    exit 3
fi

# shellcheck disable=SC2086
PYTHONPATH="$DIR" exec $PY -m malo "$@"
