"""Failure-signature computation (pure domain policy).

A failure signature is a deterministic SHA-256 over the normalized set of
blocking findings. Two iterations that report the same normalized findings
produce the same signature, which is what the no-progress detector keys on.

Normalization (order-independent, whitespace-insensitive, case-insensitive)
guarantees that a genuinely unchanged failure yields a stable hash while any
new/removed finding shifts it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def normalize_findings(findings: Iterable[str]) -> list[str]:
    """Lower-case, strip, drop blanks, de-duplicate, and sort findings."""
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in findings:
        token = " ".join(str(raw).split()).strip().lower()
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    normalized.sort()
    return normalized


def compute_failure_signature(findings: Iterable[str]) -> str:
    """Return a stable SHA-256 hex digest of the normalized findings.

    An empty finding set yields an empty signature (`""`), which the decision
    logic treats as "no comparable failure" so it never counts as no-progress.
    """
    normalized = normalize_findings(findings)
    if not normalized:
        return ""
    payload = "\n".join(normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
