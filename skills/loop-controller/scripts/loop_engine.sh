#!/bin/sh
# Portable launcher for the AIWF loop engine (POSIX sh).
#
# Resolves a Python >= 3.9 interpreter across machines that expose it as
# `python3`, `python`, or the Windows launcher `py -3`. If none is found the
# script fails with a machine-readable envelope instructing the agent to fall
# back to PROTOCOL.md (hand-execution), which yields identical results.
#
# Canonical agent-facing entrypoint remains `aiwf loop <...>`; this launcher is
# the raw-script fallback for environments without the installed `aiwf` CLI.
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
    printf '%s\n' '{"error":"NoPythonInterpreter","message":"No python3/python/py (>=3.9) found. Follow PROTOCOL.md to run the loop controller by hand.","fallback":"PROTOCOL.md"}' >&2
    exit 3
fi

# shellcheck disable=SC2086
PYTHONPATH="$DIR" exec $PY -m loop_engine "$@"
