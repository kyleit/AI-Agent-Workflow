#!/usr/bin/env python3
"""Aggregate strict code-block gate results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def aggregate(payload: dict) -> dict:
    statuses = []
    findings = list(payload.get("blocking_findings", []))
    for key in ("per_code_block", "profile_results", "materialized_scope", "architecture_results"):
        for item in payload.get(key, []):
            status = item.get("status", "BLOCKED")
            statuses.append(status)
            for finding in item.get("findings", []):
                findings.append(f"{item.get('id', key)}: {finding}")
            if item.get("finding"):
                findings.append(f"{item.get('id', key)}: {item['finding']}")
    if "BLOCKED" in statuses:
        decision = "BLOCKED"
    elif "FAIL" in statuses:
        decision = "FAIL"
    elif any(status == "PASS" for status in statuses):
        decision = "PASS"
    else:
        decision = "NOT_APPLICABLE"
    payload["decision"] = decision
    payload["blocking_findings"] = sorted(set(findings))
    payload["test_status"] = "NOT_RUN"
    stable = json.dumps({k: v for k, v in payload.items() if k != "result_sha256"}, sort_keys=True)
    payload["result_sha256"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = aggregate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
