---
artifact_type: debug
feature_id: FEAT-048
workflow: standard
status: PASS
---

# Debug Report – Provider-Centric Runtime & Usage Engine

## 1. Summary

Debug phase for FEAT-048 Phase 1 implementation on branch `feat/FEAT-048-provider-centric-engine`. Conducted Python compilation check, AST syntax validation, manual 5-test functional test suite, and a 44-test formal pytest-class suite covering all new modules. One bug was found and fixed in `NormalizedUsageRecord.__post_init__()` (token clamping order). Environment issue discovered: global `pytest` is broken by an incompatible `qmd` plugin (`rank_bm25` not importable on Python 3.14); workaround applied using direct module test runner.

---

## 2. Diagnostics

- **Build Status**: PASS (Command: `python -m py_compile` on 12 files — all 12 OK)
- **Lint Status**: NOT CONFIGURED — `ruff` and `flake8` not installed in this environment; AST parse used as fallback (all 12 files: 0 syntax errors)
- **Unit Tests Status**: PASS — 44/44 tests via direct module runner (pytest blocked by broken `qmd` plugin)

---

## 3. Issues Found & Resolved

| Issue Description | Root Cause | Fix Summary | Files Affected |
| :--- | :--- | :--- | :--- |
| `NormalizedUsageRecord` reports wrong `total_tokens` when input/output tokens are negative | `__post_init__` computed `total_tokens = input + output` **before** clamping negative values to 0, so `total_tokens` used the un-clamped values | Swapped execution order: clamp all token fields to ≥ 0 first, then compute `total_tokens` | `connectors/base.py` |
| `pytest` crashes before any tests run due to `qmd` pytest plugin failing to import `rank_bm25` | Python 3.14 incompatibility in `qmd.testing` package — `rank_bm25` is installed but not importable by `qmd` | Used direct module test runner as workaround; pre-existing environment issue, not caused by FEAT-048 | Environment only — no code fix needed |

---

## 4. Remaining Risks

- **Risk**: `ruff` / `flake8` not installed → lint cannot be enforced in CI → style regressions may accumulate → **Mitigation**: Add `ruff` to project dev-dependencies; run `pip install ruff` in environment setup.
- **Risk**: `pytest` broken by `qmd` plugin on Python 3.14 → no automated test runner → **Mitigation**: Install `rank-bm25` compatible with Python 3.14 or pin `qmd` to a compatible version; the test file `test_feat048_provider_engine.py` is ready when pytest is fixed.
- **Risk**: `AntigravityConnector.parse_conversation()` uses char/3 estimation (not provider-reported counts) → `accuracy_source = "estimated"` → **Mitigation**: This is the correct behavior per blueprint NFR-01 (Provider Reported > Estimated). Future FEAT-049 or provider API integration will upgrade to `provider_reported`.
- **Risk**: `IncrementalTranscriptReader` uses MD5 of `(path + size + mtime_ns)` for hash — not content hash → a file with same size and mtime but different content would not be re-read → **Mitigation**: Acceptable trade-off for performance; scenario is extremely rare in practice. Full content hash would be prohibitively expensive for large transcripts.

---

## 5. Debug Status

**Status**: PASS

All compilation checks pass. 1 bug identified and fixed (`NormalizedUsageRecord` clamping order). 44 unit tests pass covering all 6 core modules. No remaining blocking issues. Implementation ready for verification.

---

## Appendix: Test Coverage by Module

| Module | Tests | Result |
| :--- | :---: | :---: |
| `connectors/base.py` (NormalizedUsageRecord) | 7 | ✅ PASS |
| `normalizer.py` (UsageNormalizer) | 8 | ✅ PASS |
| `cost_engine.py` (CostEngine) | 10 | ✅ PASS |
| `connectors/__init__.py` (ConnectorRegistry) | 6 | ✅ PASS |
| `transcript_engine.py` (IncrementalTranscriptReader) | 7 | ✅ PASS |
| `connectors/antigravity.py` (AntigravityConnector) | 6 | ✅ PASS |
| **Total** | **44** | **✅ PASS** |
