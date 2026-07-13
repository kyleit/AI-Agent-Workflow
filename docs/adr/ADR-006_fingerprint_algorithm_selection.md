<!-- File path: docs/adr/ADR-006_fingerprint_algorithm_selection.md -->

# ADR-006: SHA-256 Fingerprint Algorithm for Canonical Request Identity

## Status
Accepted

## Related Feature
FEAT-049 (Transcript-First Accounting System)

## Context

FEAT-049 requires a **canonical request identity** system to eliminate double-counting across re-index, retry, copy, and resume operations. Every provider request across all 4 connectors (Antigravity, Claude Code, Cursor, VS Code Agents) must be uniquely identifiable by a deterministic fingerprint derived from the request's intrinsic properties — not a random UUID or DB auto-increment.

The following architectural drivers shaped this decision:

1. **Determinism** (NFR-01): Repeated scans of identical transcript data must produce identical fingerprints with zero drift.
2. **Dedup correctness** (FR-01, FR-12): The fingerprint must uniquely identify the same logical request across retries, conversation copies, and session resumes.
3. **Offline-first** (TC-02): The algorithm must not require network access.
4. **Pre-normalization timing** (FR-04): The fingerprint must be computed from the raw provider payload *before* normalization, so that different parsers independently produce the same fingerprint for the same request.
5. **Field ordering stability**: The canonical input to the hash function must have a fixed, deterministic ordering that does not depend on Python dict insertion order (which varies by version).
6. **Collision resistance**: The fingerprint space must be large enough that accidental collisions across a project's lifetime (expected ~10,000–100,000 requests) are negligible.

## Decision

**Use SHA-256 with a deterministic field ordering** as the fingerprint algorithm.

### Algorithm specification

```
CANONICAL_FIELDS = [
    "provider",
    "conversation_id",
    "request_id",
    "response_id",
    "model",
    "timestamp",
    "payload_hash"
]

canonical_dict = {k: fields.get(k, "") for k in CANONICAL_FIELDS}
canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
fingerprint    = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()  # 64-char lowercase hex
```

Where `payload_hash` is itself:

```
payload_hash = hashlib.sha256(
    json.dumps(raw_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
).hexdigest()[:16]   # 16-char prefix to keep fingerprint input compact
```

If `raw_payload` is unavailable (empty dict or None), `payload_hash` defaults to `""`.

### Deduplication collision policy

When `FingerprintEngine.register()` detects a matching fingerprint:
- The existing record is **not** updated or overwritten.
- `duplicate_count` in `request_fingerprints` is incremented by 1.
- `last_seen` timestamp is updated to the current time.
- The parse pipeline receives `None` from `parse_with_fingerprint()` and skips the record.
- `ReconciliationReport.duplicates_ignored` is incremented.

### Pre-normalization timing contract

`compute_fingerprint()` **must** be called on the raw provider payload line **before** any field normalization (token count clamping, accuracy source assignment, model name canonicalization). This is enforced in `ITranscriptParser.parse_with_fingerprint()` — fingerprint is the first operation, normalization follows.

### Storage format

- Fingerprint stored as `TEXT PRIMARY KEY` (64-char lowercase hex) in `request_fingerprints` table.
- Also stored in `provider_requests.fingerprint TEXT` (additive column, NULL for pre-FEAT-049 records).
- Validated as `r"^[0-9a-f]{64}$"` on write; invalid values set to `NULL`.

## Alternatives Considered

### Option A: UUID v4 (random)
- **Rejected**: Non-deterministic. Two scans of the same transcript line produce different UUIDs, making deduplication impossible. Violates NFR-01 (determinism).

### Option B: MD5
- **Rejected**: MD5 is cryptographically broken (known collision attacks). Although collision attacks in this domain are low-risk (no adversarial input), MD5 is deprecated on many enterprise systems and may be blocked by FIPS-140 environments. SHA-256 has no known practical collisions.

### Option C: SHA-1
- **Rejected**: SHA-1 is deprecated for new systems since 2017 (NIST SP 800-131A). Same collision risk concern as MD5.

### Option D: BLAKE3
- **Rejected for now**: BLAKE3 is faster than SHA-256 and has no known weaknesses, but it requires a third-party Python package (`blake3`) not bundled in the standard library. FEAT-049 has a strong offline-first, zero-external-dependency constraint (TC-02). Can be revisited in a future ADR if performance profiling shows SHA-256 as a bottleneck.

### Option E: Full content hash only (no field ordering)
- **Rejected**: A hash of only the raw payload is insufficient. Two requests from different providers with the same payload content (e.g., both returning the same model response) would produce the same fingerprint — creating false duplicate detection. Provider + conversation_id + request_id context must be included.

### Option F: Database auto-increment ID
- **Rejected**: Auto-increment IDs are not portable across re-index cycles or database migrations. A new scan would assign different IDs to the same requests.

## Trade-offs

| Criterion | SHA-256 (selected) | UUID v4 | BLAKE3 |
| :--- | :--- | :--- | :--- |
| Determinism | ✅ Always deterministic | ❌ Random | ✅ Always deterministic |
| Dedup correctness | ✅ Correct | ❌ Impossible | ✅ Correct |
| Collision resistance | ✅ 2^256 space | — | ✅ 2^256 space |
| Standard library | ✅ `hashlib` (built-in) | ✅ `uuid` (built-in) | ❌ Third-party (`blake3`) |
| Performance | ✅ < 1ms per hash | — | ✅ ~3x faster |
| FIPS compatibility | ✅ Approved | — | ❌ Not FIPS-certified |
| Offline-first | ✅ Yes | ✅ Yes | ✅ Yes |

**SHA-256 is the optimal choice**: deterministic, collision-resistant, zero external dependencies, FIPS-compatible, and sufficiently fast for the NFR-02 performance targets (10,000 requests < 30s full scan, incremental < 1s).

## Consequences

### Positive
- `FingerprintEngine.compute()` is a pure function with no side effects and no DB access — easy to test and audit.
- Fingerprints are stable across Python versions (SHA-256 output is spec-defined, not implementation-defined).
- The `request_fingerprints` table becomes a permanent, human-readable audit trail of all unique requests.
- Historical re-scans of unchanged transcript data produce zero new fingerprints (NFR-01 determinism, NFR-03 idempotency).

### Negative
- SHA-256 adds ~0.1–0.5ms per request. For 10,000 requests, this adds ~1–5s overhead. Acceptable given the 30s budget (NFR-02). Profiled in `test_transcript_performance.py`.
- Pre-normalization timing is a strict contract. If a connector accidentally normalizes fields before calling `compute_fingerprint()`, the fingerprint will differ from the canonical value. Enforced by `ITranscriptParser.parse_with_fingerprint()` ordering.
- Fingerprints of pre-FEAT-049 records in `provider_requests` will be `NULL`. These are grandfathered records; `usage doctor` will flag them as `missing_fingerprint` in its output.

### Future Considerations
- If BLAKE3 becomes available as a standard-library module (or if offline constraint is relaxed), it can supersede SHA-256 via a new ADR without data migration (fingerprints are recomputable from transcripts).
- The 16-char `payload_hash` prefix may be shortened or eliminated if profiling shows the full payload hashing is a bottleneck for very large request payloads.

## Risks

| Risk | Likelihood | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| Pre-norm timing violation in new connector | Low | High (false duplicates) | `ITranscriptParser` interface enforces ordering; `test_connectors.py` validates |
| SHA-256 performance bottleneck at 10k+ requests | Low | Medium | `test_transcript_performance.py` benchmark gate; BLAKE3 migration path if needed |
| Grandfathered NULL fingerprints confuse dedup | Medium | Low | `usage doctor` flags them; no silent suppression |
| Python version differences in `json.dumps` ordering | None | None | `sort_keys=True` and `separators` params ensure deterministic output |

## References

- [FEAT-049 Brainstorming](../brainstorming/FEAT-049_transcript_first_accounting_system.md) — FR-01, FR-12, NFR-01, TC-02, TC-03
- [FEAT-049 Implementation Plan](../plans/FEAT-049_transcript_first_accounting_system_plan.md) — Task 1.1
- [FEAT-049 Technical Blueprint](../designs/FEAT-049_transcript_first_accounting_system_blueprint.md) — Section 3.1 (FingerprintEngine), Section 4.1 (interface contract), Section 6.1 (request_fingerprints table)
- [ADR-005: Runtime Event Bus](ADR-005_runtime_event_bus_and_streaming_protocol.md) — parent architecture (SQLite WAL mode, offline-first constraints)
- Python `hashlib` documentation: https://docs.python.org/3/library/hashlib.html
- NIST FIPS 180-4 (SHA-256 specification): https://csrc.nist.gov/publications/detail/fips/180/4/final
