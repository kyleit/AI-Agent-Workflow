<!-- File path: docs/designs/FEAT-049_transcript_first_accounting_system_blueprint.md -->

---
feature_id: FEAT-049
feature_name: Transcript-First Accounting System
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-049_transcript_first_accounting_system_plan.md
next_artifact: Implementation (Source Code)
---

# Technical Design Blueprint & Implementation Contract
# FEAT-049: Transcript-First Accounting System

## 0. Baseline Context & References

- **Memory Baseline**: High confidence. FEAT-048 fully implemented (5 phases, 71 tests passing). Source files inspected directly.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/connectors/base.py` (L1-192) — NormalizedUsageRecord (15 fields), ProviderConnector ABC
  - `skills/workflow-runtime/scripts/db.py` (L1-800) — init_db_schema(), provider_requests table, FEAT-048 additive migrations pattern
  - `skills/workflow-runtime/scripts/cost_engine.py` (L1-80) — CostEngine, CostResult, ModelPricing, CostBreakdown
  - `skills/workflow-runtime/scripts/transcript_engine.py` (L1-80) — IncrementalTranscriptReader.read_new_lines(), cursor tracking
- **Key Findings from Source Inspection**:
  - `read_new_lines()` currently returns `List[dict]`. Must be extended to `List[Tuple[dict, int]]` (breaking change for callers).
  - `NormalizedUsageRecord.__post_init__` enforces non-negative counts and recomputes total_tokens. New tool_tokens must NOT be added to total_tokens.
  - `db.py` uses `try/except OperationalError` pattern for additive `ALTER TABLE` — proven idempotent across all existing migrations.
  - `CostEngine` has no `db_conn` dependency. Adding it must be optional (None default) to avoid breaking 71 FEAT-048 tests.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/fingerprint_engine.py` | NEW | SHA-256 fingerprint + dedup lookup | db.py (request_fingerprints) | Low — isolated new module |
| `skills/workflow-runtime/scripts/reconciliation_engine.py` | NEW | Sync engine, ReconciliationReport (8 fields) | fingerprint_engine, db.py | Low — isolated new module |
| `skills/workflow-runtime/scripts/usage_validator.py` | NEW | CLI: validate / reconcile / doctor / diff | reconciliation_engine, db.py | Low — CLI wrapper only |
| `skills/workflow-runtime/scripts/connectors/base.py` | MODIFY | NormalizedUsageRecord +4 fields; ITranscriptParser ABC | None (backward-safe defaults) | Low — additive dataclass fields |
| `skills/workflow-runtime/scripts/connectors/antigravity.py` | MODIFY | Implement ITranscriptParser; add tool_tokens extraction | base.py ITranscriptParser | Medium — adds pre-norm fingerprint |
| `skills/workflow-runtime/scripts/connectors/claude_code.py` | MODIFY | Implement ITranscriptParser; add tool_tokens extraction | base.py ITranscriptParser | Medium |
| `skills/workflow-runtime/scripts/connectors/cursor.py` | MODIFY | Implement ITranscriptParser; tool_tokens fallback 0 | base.py ITranscriptParser | Medium — unstructured payload |
| `skills/workflow-runtime/scripts/connectors/vscode_agents.py` | MODIFY | Implement ITranscriptParser; tool_tokens fallback 0 | base.py ITranscriptParser | Medium — unstructured payload |
| `skills/workflow-runtime/scripts/transcript_engine.py` | MODIFY | read_new_lines() -> List[Tuple[dict,int]] with offset | None | Medium — callers must be updated |
| `skills/workflow-runtime/scripts/cost_engine.py` | MODIFY | Add pricing_version param, effective_date lookup, historical lock | db.py pricing_versions | Medium — extends calculate() |
| `skills/workflow-runtime/scripts/db.py` | MODIFY | 3 new tables + 4 additive columns + batch insert + indexes | None | Low — proven idempotent pattern |
| `skills/workflow-runtime/scripts/provider_engine.py` | MODIFY | Wire FingerprintEngine into parse pipeline | fingerprint_engine, reconciliation_engine | Medium — touches core pipeline |
| `skills/workflow-runtime/data/pricing.json` | MODIFY | Add version + effective_date per model entry | None | Low — additive JSON fields |
| `extensions/visualizer/resources/webview.html` | MODIFY | Extend AccuracyBadge CSS; add Reconciliation Report panel | None | Low — CSS + HTML only |
| `extensions/visualizer/src/extension.ts` | MODIFY | getProviderUsage() + UPDATE_RECONCILIATION handler | webview.html message types | Medium — TypeScript change |
| `extensions/visualizer/src/webviewHtml.ts` | Do Not Modify | Auto-generated from webview.html via node build.js | webview.html | None |
| `skills/workflow-runtime/tests/test_fingerprint_engine.py` | NEW | SHA-256 stability, dedup, collision policy | fingerprint_engine | None |
| `skills/workflow-runtime/tests/test_reconciliation_engine.py` | NEW | 8-field report, idempotency, confidence score | reconciliation_engine | None |
| `skills/workflow-runtime/tests/test_usage_validator.py` | NEW | 4 CLI commands, impossible value detection | usage_validator | None |
| `skills/workflow-runtime/tests/test_versioned_pricing.py` | NEW | historical lock, effective_date range lookup | cost_engine | None |
| `skills/workflow-runtime/tests/test_transcript_first_pipeline.py` | NEW | Integration: transcript -> fingerprint -> normalize -> cost -> reconcile | All Phase 1+2 | None |
| `skills/workflow-runtime/tests/test_stress_suite.py` | NEW | 100 convs, 10k requests, 3x determinism | All modules | None |
| `skills/workflow-runtime/tests/test_db_schema.py` | MODIFY | Add 3 new tables + 4 new column schema tests | db.py | None |
| `skills/workflow-runtime/tests/test_normalization.py` | MODIFY | Add 4 new NormalizedUsageRecord field tests | connectors/base.py | None |
| `skills/workflow-runtime/tests/test_connectors.py` | MODIFY | Add ITranscriptParser interface tests for 4 connectors | connectors/ | None |
| `skills/workflow-runtime/tests/test_transcript_performance.py` | MODIFY | Add 10k request benchmark | transcript_engine | None |
| `docs/adr/ADR-006_fingerprint_algorithm_selection.md` | NEW | SHA-256 algorithm choice, field ordering, pre-norm timing | None | None |
| `.agents/memory/project-summary.md` | MODIFY | Add FEAT-049 modules to Main Modules | None | None |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/
  scripts/
    fingerprint_engine.py          [NEW]
    reconciliation_engine.py       [NEW]
    usage_validator.py             [NEW]
    connectors/
      base.py                      [MODIFY: NormalizedUsageRecord v2 + ITranscriptParser]
      antigravity.py               [MODIFY]
      claude_code.py               [MODIFY]
      cursor.py                    [MODIFY]
      vscode_agents.py             [MODIFY]
    transcript_engine.py           [MODIFY: +transcript_offset output]
    cost_engine.py                 [MODIFY: +versioned pricing]
    provider_engine.py             [MODIFY: wire FingerprintEngine]
    db.py                          [MODIFY: +3 tables +4 columns +batch +indexes]
  data/
    pricing.json                   [MODIFY: +version +effective_date]
  tests/
    test_fingerprint_engine.py     [NEW]
    test_reconciliation_engine.py  [NEW]
    test_usage_validator.py        [NEW]
    test_versioned_pricing.py      [NEW]
    test_transcript_first_pipeline.py [NEW]
    test_stress_suite.py           [NEW]
    test_db_schema.py              [MODIFY]
    test_normalization.py          [MODIFY]
    test_connectors.py             [MODIFY]
    test_transcript_performance.py [MODIFY]
extensions/visualizer/
  resources/
    webview.html                   [MODIFY]
  src/
    extension.ts                   [MODIFY]
    webviewHtml.ts                 [Do Not Modify - auto-generated]
docs/
  adr/
    ADR-006_fingerprint_algorithm_selection.md [NEW]
```

---

## 3. Complete Class & Module Design

### 3.1 `FingerprintEngine` (fingerprint_engine.py)

- **Responsibilities**: Compute deterministic SHA-256 fingerprint from raw provider payload fields. Check and register fingerprints in request_fingerprints table.
- **Constructor Parameters**: `db_conn: sqlite3.Connection`
- **Public Methods**:
  - `compute(fields: dict) -> str` — 64-char hex SHA-256. Field ordering: `["provider", "conversation_id", "request_id", "response_id", "model", "timestamp", "payload_hash"]`. Missing fields = empty string. Never raises.
  - `is_duplicate(fingerprint: str) -> bool` — lookup request_fingerprints. Returns True if exists.
  - `register(fingerprint: str, metadata: dict) -> bool` — INSERT OR IGNORE. On conflict: UPDATE duplicate_count += 1, last_seen = now. Returns True if new, False if duplicate.
  - `get_stats() -> dict` — `{"total_registered": int, "total_duplicates": int}`
- **Internal Methods**:
  - `_canonical_string(fields: dict) -> str` — deterministic JSON with sorted keys
  - `_compute_payload_hash(raw_payload: dict) -> str` — SHA-256 of `json.dumps(raw_payload, sort_keys=True).encode()`
- **Dependencies**: `hashlib`, `json`, `sqlite3`

### 3.2 `ITranscriptParser` ABC (connectors/base.py — new abstract class)

- **Responsibilities**: Define contract for provider-specific transcript parsing with fingerprint support.
- **Note**: Does NOT inherit from ProviderConnector. Separate interface. Connectors implement both.
- **Abstract Methods**:
  - `compute_fingerprint(raw_line: dict) -> str`
  - `extract_tool_tokens(raw_line: dict) -> int` — returns 0 if unavailable
  - `get_usage_source(raw_line: dict) -> str` — one of ACCURACY_PRIORITY values
  - `parse_with_fingerprint(raw_line: dict, offset: int, fp_engine: "FingerprintEngine") -> Optional[NormalizedUsageRecord]` — full parse; returns None if duplicate

### 3.3 `NormalizedUsageRecord v2` (connectors/base.py — extended dataclass)

**4 New Fields** (backward-safe defaults):
```python
fingerprint: Optional[str] = None          # 64-char hex SHA-256 or None
tool_tokens: int = 0                        # tool call tokens; NOT added to total_tokens
transcript_offset: int = -1                 # byte offset in source file; -1 if untracked
raw_metadata: Optional[dict] = None        # extra provider-specific metadata
```

**Updated `__post_init__`**:
- Clamp `tool_tokens` (non-negative), same pattern as other token fields.
- Validate `fingerprint`: must be `None` or match `r"^[0-9a-f]{64}$"`. If invalid: set to None.
- Extend valid `accuracy_source` set: add `"response_payload"`, `"api_metadata"`, `"deterministic_reconstruction"`, `"tokenizer"`.
- `total_tokens` computation unchanged: `input_tokens + output_tokens` (tool_tokens excluded).

### 3.4 `ReconciliationEngine` (reconciliation_engine.py)

- **Constructor Parameters**: `db_conn: sqlite3.Connection, connector_registry: ConnectorRegistry`
- **Public Methods**:
  - `sync(transcript_paths: List[str] = None) -> ReconciliationReport` — idempotent. Each call inserts new report row (not update).
  - `get_last_report() -> Optional[ReconciliationReport]`
  - `get_report_by_id(report_id: int) -> Optional[ReconciliationReport]`
- **Internal Methods**:
  - `_process_transcript(file_path: str) -> dict`
  - `_compute_confidence(stats: dict) -> float` — `parsed / max(1, parsed+corrupted+missing_metadata)`, clamped [0.0, 1.0]
  - `_persist_report(report: ReconciliationReport) -> int`

### 3.5 `ReconciliationReport` (reconciliation_engine.py — dataclass)

```python
@dataclass
class ReconciliationReport:
    report_id: Optional[int]        # DB row id (None before persist)
    timestamp: str                  # ISO8601
    requests_discovered: int        # total lines seen in transcripts
    requests_parsed: int            # successfully normalized
    duplicates_ignored: int         # fingerprint already in request_fingerprints
    corrupted_transcripts: int      # lines that failed JSON parse
    missing_usage_metadata: int     # lines with no token data
    reconstructed_usage: int        # accuracy_source = deterministic_reconstruction
    estimated_usage: int            # accuracy_source = estimated
    confidence_score: float         # [0.0, 1.0]
    duration_ms: int
    def to_dict(self) -> dict: ...
```

### 3.6 `CostEngine v2` (cost_engine.py — extended)

- **Extended Constructor**: `def __init__(self, pricing_path: str = None, db_conn: sqlite3.Connection = None)` — db_conn optional; if None, versioned pricing disabled (backward compat).
- **Extended `calculate()` signature**:
  ```python
  def calculate(
      self,
      record: NormalizedUsageRecord,
      request_timestamp: Optional[str] = None,
      pricing_version: Optional[str] = None
  ) -> CostResult
  ```
  Priority: explicit pricing_version > effective_date lookup by timestamp > current pricing.json.
- **New Public Methods**:
  - `get_pricing_version(provider: str, model: str, timestamp: str) -> Optional[str]`
  - `lock_cost(conn: sqlite3.Connection, request_id: str, cost_result: CostResult, pricing_version: str) -> None` — UPDATE WHERE `pricing_version IS NULL OR pricing_version = ''`
- **Extended `CostResult`**: add `pricing_version: str = ""` field.
- **Extended `CostBreakdown`**: add `tool_cost: float = 0.0` field.
- **Extended `ModelPricing`**: add `tool_per_mtok: float = 0.0` field.

### 3.7 `UsageValidator` (usage_validator.py)

- **Constructor Parameters**: `db_conn: sqlite3.Connection`
- **Public Methods**:
  - `validate(conn) -> ValidationResult` — checks: no negative tokens, total >= input+output, no empty model, no future timestamps.
  - `reconcile(conn) -> ReconciliationReport` — delegates to ReconciliationEngine.sync(). Idempotent.
  - `doctor(conn) -> DoctorReport` — runs validate() + impossible value detection + actionable suggestions.
  - `diff(conn, run_id_a: int, run_id_b: int) -> DiffReport` — arithmetic delta for each 8-field metric.
- **CLI Entry Point**: argparse with subcommands `validate | reconcile | doctor | diff`
- **Exit Codes**: 0 = clean, 1 = violations, 2 = fatal.

---

## 4. Detailed Interface Contracts

### 4.1 `FingerprintEngine.compute(fields: dict) -> str`
- **Algorithm**: `hashlib.sha256(json.dumps({k: fields.get(k,"") for k in CANONICAL_FIELDS}, sort_keys=True).encode()).hexdigest()`
- **CANONICAL_FIELDS**: `["provider", "conversation_id", "request_id", "response_id", "model", "timestamp", "payload_hash"]`
- **Output**: 64-char lowercase hex. Pattern: `r"^[0-9a-f]{64}$"`. Never raises.
- **payload_hash**: Computed as `hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()[:16]` if raw_payload present, else empty string.

### 4.2 `FingerprintEngine.register(fingerprint: str, metadata: dict) -> bool`
- **Returns**: `True` if new record inserted, `False` if duplicate.
- **On duplicate**:
  ```sql
  UPDATE request_fingerprints
  SET duplicate_count = duplicate_count + 1, last_seen = ?
  WHERE fingerprint = ?
  ```
- **On new**: `INSERT OR IGNORE INTO request_fingerprints (...) VALUES (...)`
- **Exceptions**: sqlite3.Error → raise `FingerprintEngineError`.

### 4.3 `IncrementalTranscriptReader.read_new_lines(file_path) -> List[Tuple[dict, int]]`
- **Breaking Change**: Return type `List[dict]` -> `List[Tuple[dict, int]]`.
- **Offset**: byte position of the START of each line (`f.tell()` before `readline()` in `rb` mode).
- **CRLF handling**: Open in `rb` mode; decode each line as `line.decode("utf-8").rstrip("\r\n")`.
- **Callers to update**: `provider_engine.py` — unpack as `(line_dict, offset)`.
- **Backward compat in tests**: Update `test_transcript_engine.py` to unpack tuples.

### 4.4 `CostEngine v2.calculate()` priority ladder
1. If `pricing_version` param provided: lookup `pricing_versions` table for exact version.
2. Elif `request_timestamp` provided: `SELECT ... WHERE provider=? AND model=? AND effective_date <= ? ORDER BY effective_date DESC LIMIT 1`
3. Else: use current `pricing.json` (existing FEAT-048 behavior).
4. `tool_cost = record.tool_tokens / 1_000_000 * pricing.tool_per_mtok` (default 0.0).
5. On pricing lookup failure: fallback to current, `CostResult.fallback_used = True`, log WARNING.

### 4.5 `UsageValidator` CLI contract
```
python usage_validator.py validate [--db PATH]
  stdout: {"status": "ok"|"violations", "violations": [...], "count": int}
  exit: 0=ok, 1=violations, 2=fatal

python usage_validator.py reconcile [--db PATH]
  stdout: ReconciliationReport as JSON
  exit: 0=ok, 2=fatal

python usage_validator.py doctor [--db PATH]
  stdout: {"violations": [...], "suggestions": [...], "confidence_score": float}
  exit: 0 always

python usage_validator.py diff --run-a INT --run-b INT [--db PATH]
  stdout: {"delta": {"requests_discovered": int, ...}, "run_a": {...}, "run_b": {...}}
  exit: 0=ok, 2=run_id not found
```

---

## 5. Configuration Schema

### 5.1 pricing.json — Extended Schema (v2.0)
```json
{
  "schema_version": "2.0",
  "default_version": "1.0.0",
  "providers": {
    "antigravity": {
      "models": {
        "gemini-2.5-pro": {
          "version": "1.0.0",
          "effective_date": "2026-01-01",
          "input_per_mtok": 1.25,
          "output_per_mtok": 10.0,
          "cache_read_per_mtok": 0.31,
          "cache_write_per_mtok": 4.5,
          "thinking_per_mtok": 3.5,
          "tool_per_mtok": 0.0
        }
      }
    }
  }
}
```
- **Migration Rule**: Entries without version/effective_date treated as version="1.0.0", effective_date="2026-01-01" (bootstrap default).
- **Validation**: effective_date = `YYYY-MM-DD`. version = semver `X.Y.Z`. tool_per_mtok optional (default 0.0).

### 5.2 DB Schema Extensions (provider_requests — 4 additive columns)
```sql
-- All via try/except OperationalError (idempotent):
ALTER TABLE provider_requests ADD COLUMN fingerprint TEXT;
ALTER TABLE provider_requests ADD COLUMN pricing_version TEXT DEFAULT '';
ALTER TABLE provider_requests ADD COLUMN tool_tokens INTEGER DEFAULT 0;
ALTER TABLE provider_requests ADD COLUMN transcript_offset INTEGER DEFAULT -1;
```

---

## 6. Database & Storage Design

### 6.1 New Table: `request_fingerprints`
```sql
CREATE TABLE IF NOT EXISTS request_fingerprints (
    fingerprint     TEXT PRIMARY KEY,
    provider        TEXT NOT NULL,
    conv_id         TEXT NOT NULL,
    request_id      TEXT NOT NULL,
    model           TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fingerprints_hash
    ON request_fingerprints (fingerprint);
CREATE INDEX IF NOT EXISTS idx_fingerprints_conv
    ON request_fingerprints (conv_id);
```

### 6.2 New Table: `pricing_versions`
```sql
CREATE TABLE IF NOT EXISTS pricing_versions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    provider             TEXT NOT NULL,
    model                TEXT NOT NULL,
    version              TEXT NOT NULL,
    effective_date       TEXT NOT NULL,
    input_per_mtok       REAL NOT NULL DEFAULT 0.0,
    output_per_mtok      REAL NOT NULL DEFAULT 0.0,
    cache_read_per_mtok  REAL NOT NULL DEFAULT 0.0,
    cache_write_per_mtok REAL NOT NULL DEFAULT 0.0,
    thinking_per_mtok    REAL NOT NULL DEFAULT 0.0,
    tool_per_mtok        REAL NOT NULL DEFAULT 0.0,
    created_at           TEXT NOT NULL,
    UNIQUE (provider, model, version)
);
CREATE INDEX IF NOT EXISTS idx_pricing_versions_effective
    ON pricing_versions (provider, model, effective_date DESC);
```

### 6.3 New Table: `reconciliation_reports`
```sql
CREATE TABLE IF NOT EXISTS reconciliation_reports (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp               TEXT NOT NULL,
    requests_discovered     INTEGER NOT NULL DEFAULT 0,
    requests_parsed         INTEGER NOT NULL DEFAULT 0,
    duplicates_ignored      INTEGER NOT NULL DEFAULT 0,
    corrupted_transcripts   INTEGER NOT NULL DEFAULT 0,
    missing_usage_metadata  INTEGER NOT NULL DEFAULT 0,
    reconstructed_usage     INTEGER NOT NULL DEFAULT 0,
    estimated_usage         INTEGER NOT NULL DEFAULT 0,
    confidence_score        REAL NOT NULL DEFAULT 0.0,
    duration_ms             INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reconciliation_timestamp
    ON reconciliation_reports (timestamp DESC);
```

### 6.4 Batch Insert Helper (db.py — new function)
```python
def batch_insert_provider_requests(
    conn: sqlite3.Connection,
    records: list[dict],
    batch_size: int = 1000
) -> int:
    """INSERT OR IGNORE in batches. Returns count inserted."""
```

### 6.5 Migration & Rollback Strategy
- **Forward**: All CREATE IF NOT EXISTS + try/except ALTER TABLE. Safe on existing DB.
- **Rollback (tables)**: `DROP TABLE IF EXISTS request_fingerprints; DROP TABLE IF EXISTS pricing_versions; DROP TABLE IF EXISTS reconciliation_reports;` — data re-indexable from transcripts.
- **Rollback (columns)**: Not reversible in SQLite without table recreation. Columns with defaults are safe to leave.

---

## 7. Cache Architecture

- **FingerprintEngine**: No in-memory cache — all lookups via SQLite WAL (correct > fast).
- **CostEngine v2**: Extend `self._data` cache to hold `pricing_versions` dict keyed by `(provider, model, version)`. Invalidated on `is_stale()`.
- **ReconciliationEngine**: No caching — each sync() reads directly from transcript files and DB.
- **TTL**: Not applicable.
- **Warmup**: CostEngine lazy-loads on first `calculate()` call (existing pattern).

---

## 8. Error Model

| Exception | Trigger | Recovery | Log Level |
| :--- | :--- | :--- | :--- |
| `FingerprintEngineError(RuntimeError)` | hashlib unavailable, SQLite write failure | Return None fingerprint, accuracy_source = estimated | ERROR |
| `ReconciliationError(RuntimeError)` | DB write failure, registry unavailable | Return partial report with confidence_score = 0.0 | ERROR |
| `PricingVersionNotFoundError(LookupError)` | No pricing_versions row matches lookup | Fallback to current pricing.json, fallback_used=True | WARNING |
| `TranscriptCorruptionWarning` (non-raising) | JSON parse fails on transcript line | Skip line, increment corrupted_transcripts | WARNING |
| `ImpossibleValueWarning` (non-raising) | Negative tokens, total < input+output, empty model, future timestamp | Flag in DoctorReport only, do not skip/correct | WARNING |

---

## 9. Skill Integration Contracts

### workflow-runtime skill
- **Before Hooks**: `fingerprint_engine.py` importable before any provider parse cycle.
- **After Hooks**: `ReconciliationEngine.sync()` called by `provider_engine.py` after every parse cycle.
- **Runtime Calls**: `usage_validator.py reconcile` called by extension.ts on 5-min timer.
- **Data Exchanged**: `provider_engine.py` outputs `{"reconciliation_summary": {report_id, timestamp, confidence_score, provider_reported_pct, derived_pct, estimated_pct, duplicates, last_scan}}` alongside existing usage JSON.

### Extensions (visualizer)
- **New Message Type**: `UPDATE_RECONCILIATION`
  - Payload: `{report_id, timestamp, confidence_score, provider_reported_pct, derived_pct, estimated_pct, duplicates_ignored, last_scan}`
- **Polling**: `updateDiagnosticsData()` extended to call `usage reconcile` on same 5-min timer.
- **AccuracyBadge CSS new classes**:
  - `.accuracy-badge.tool-estimated` — grey (tool_tokens accuracy = estimated)
  - Existing: `.accuracy-badge.provider-reported` (green), `.accuracy-badge.derived` (yellow), `.accuracy-badge.estimated` (red)

---

## 10. CLI & Runtime Contracts

### `usage_validator.py` — Standalone CLI
```
python usage_validator.py validate [--db PATH]
python usage_validator.py reconcile [--db PATH]
python usage_validator.py doctor [--db PATH]
python usage_validator.py diff --run-a INT --run-b INT [--db PATH]
```
- Default `--db`: `.agents/project_runtime.db`
- All output: JSON to stdout, human-readable summary to stderr.

### `provider_engine.py` — New `usage` subcommand group
```
python provider_engine.py usage validate
python provider_engine.py usage reconcile
python provider_engine.py usage doctor
python provider_engine.py usage diff --run-a INT --run-b INT
python provider_engine.py usage reprice
```
- `reprice` subcommand: recomputes cost for all unlocked rows using latest pricing.json. Requires explicit user invocation.

---

## 11. Sequence Flows

### 11.1 Normal Parse Flow (Phase 1 + 2 integrated)
```
provider_engine.py parse
  -> ConnectorRegistry.detect_providers()
  -> for each provider:
       connector.parse_with_fingerprint(raw_line, offset, fp_engine)
         -> FingerprintEngine.compute(fields) => fingerprint
         -> FingerprintEngine.is_duplicate(fingerprint) => False
         -> FingerprintEngine.register(fingerprint, metadata) => True (new)
         -> NormalizedUsageRecord v2 built (fingerprint, tool_tokens, offset)
         -> CostEngine v2.calculate(record, timestamp) => CostResult (versioned)
         -> CostEngine.lock_cost(conn, request_id, cost_result, pricing_version)
         -> batch_insert_provider_requests(conn, [record])
  -> ReconciliationEngine.sync() => ReconciliationReport
  -> output: usage JSON + reconciliation_summary
```

### 11.2 Duplicate Detection Flow
```
FingerprintEngine.compute(fields) => fingerprint F
FingerprintEngine.is_duplicate(F) => True
FingerprintEngine.register(F, metadata) => False (duplicate_count += 1)
parse_with_fingerprint() => None (skip)
ReconciliationEngine: duplicates_ignored += 1
```

### 11.3 Incremental Rescan (no new data)
```
IncrementalTranscriptReader.read_new_lines(file_path)
  -> file_hash unchanged => return []
ReconciliationEngine.sync() => report with requests_discovered = 0
New row inserted in reconciliation_reports (not overwrite)
```

### 11.4 Historical Cost Lock Flow (usage reprice)
```
usage_validator.py reprice (explicit user command)
  -> CostEngine loads latest pricing.json
  -> for each provider_requests row WHERE pricing_version IS NULL or '':
       new_cost = CostEngine.calculate(record) using latest pricing
       UPDATE provider_requests SET cost_usd = new_cost, pricing_version = 'reprice-2026-07-10'
  -> INSERT new pricing_versions snapshot
```

### 11.5 Corrupted Transcript Line
```
IncrementalTranscriptReader: json.loads() fails on line at offset O
  -> raise TranscriptParseError (caught internally)
  -> skip line, advance offset past it
ReconciliationEngine: corrupted_transcripts += 1
  -> log WARNING with file_path, offset O, raw_line[:200]
```

---

## 12. Security & Safety

- **Workspace Boundary**: All new scripts write only to `.agents/project_runtime.db`. No writes outside workspace.
- **Path Validation**: All `file_path` args resolved via `os.path.abspath()`. CLI `--db PATH` validated to be within workspace before connect.
- **Forbidden directories**: `/tmp`, `C:\Windows`, any path outside workspace root.
- **SHA-256 Safety**: Only provider metadata hashed. No secrets. No timing attack surface.
- **Historical Cost Lock Guard**: `lock_cost()` uses `WHERE pricing_version IS NULL OR pricing_version = ''` — cannot overwrite a locked cost row.
- **Rollback Safety**: All DB migrations use IF NOT EXISTS / try-except — failed migration never corrupts existing data.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit | test_fingerprint_engine.py | FingerprintEngine | Same fingerprint across re-index, retry, copy |
| FR-01 | Unit | test_fingerprint_engine.py | FingerprintEngine | Output matches `r"^[0-9a-f]{64}$"` |
| FR-02 | Unit | test_normalization.py | NormalizedUsageRecord v2 | accuracy_source in ACCURACY_PRIORITY_LADDER |
| FR-03 | Unit | test_connectors.py | All 4 connectors | isinstance(connector, ITranscriptParser) True |
| FR-04 | Unit | test_normalization.py | NormalizedUsageRecord v2 | All 4 new fields present with correct defaults |
| FR-05 | Unit | test_normalization.py | NormalizedUsageRecord v2 | raw_metadata preserved in to_dict() |
| FR-06 | Unit | test_transcript_engine.py | IncrementalTranscriptReader | 2nd scan of unchanged file returns [] |
| FR-06 | Unit | test_transcript_engine.py | IncrementalTranscriptReader | Returns List[Tuple[dict,int]], offset >= 0 |
| FR-07 | Unit | test_reconciliation_engine.py | ReconciliationEngine | Report has all 8 fields non-None |
| FR-07 | Unit | test_reconciliation_engine.py | ReconciliationEngine | sync() twice on same data = identical reports |
| FR-08 | Unit | test_versioned_pricing.py | CostEngine v2 | Old cost unchanged after pricing.json update |
| FR-08 | Unit | test_versioned_pricing.py | CostEngine v2 | get_pricing_version() returns nearest effective_date |
| FR-09 | Unit | test_normalization.py | NormalizedUsageRecord v2 | accuracy_source maps to correct badge class |
| FR-10 | Integration | test_transcript_first_pipeline.py | Dashboard | provider_reported_pct + derived_pct + estimated_pct = 100.0 |
| FR-11 | Unit | test_usage_validator.py | UsageValidator | validate() exit 0 on clean data |
| FR-11 | Unit | test_usage_validator.py | UsageValidator | reconcile() idempotent (2nd call = same output) |
| FR-11 | Unit | test_usage_validator.py | UsageValidator | doctor() returns suggestions for impossible values |
| FR-11 | Unit | test_usage_validator.py | UsageValidator | diff() returns delta dict for 2 run IDs |
| FR-12 | Unit | test_fingerprint_engine.py | FingerprintEngine | register() twice: 2nd False, duplicate_count=1 |
| FR-12 | Integration | test_transcript_first_pipeline.py | Full pipeline | Retry request not double-counted in totals |
| FR-13 | Unit | test_usage_validator.py | UsageValidator.doctor() | Flags negative token count |
| FR-13 | Unit | test_usage_validator.py | UsageValidator.doctor() | Flags total < input+output |
| FR-13 | Unit | test_usage_validator.py | UsageValidator.doctor() | Flags empty model field |
| FR-14 | Unit | test_versioned_pricing.py | CostEngine v2 | lock_cost() does not overwrite locked cost |
| NFR-01 | Stress | test_stress_suite.py | All modules | 3x identical full scan = identical totals (zero drift) |
| NFR-02 | Performance | test_transcript_performance.py | Reader + FingerprintEngine | 10k requests < 30s |
| NFR-02 | Performance | test_transcript_performance.py | Reader | Incremental rescan < 1s |
| NFR-03 | Unit | test_reconciliation_engine.py | ReconciliationEngine | sync() N times = same confidence_score |
| NFR-05 | Regression | (all 71 FEAT-048 tests) | Full FEAT-048 surface | All 71 pass after Phase 1 changes |
| NFR-06 | Stress | test_stress_suite.py | All modules | 100 convs, 10k mixed-provider, deterministic |
| TC-03 | Unit | test_fingerprint_engine.py | FingerprintEngine | compute() output matches SHA-256 regex |
| TC-04 | Compatibility | test_db_schema.py | db.py | init_db_schema() idempotent for new tables+columns |
| AC-01 | Stress | test_stress_suite.py | All | 3 scans, zero drift |
| AC-02 | Integration | test_transcript_first_pipeline.py | FingerprintEngine | Duplicate not double-counted |
| AC-03 | Integration | test_transcript_first_pipeline.py | Dashboard | % sum = 100% |
| AC-04 | Unit | test_versioned_pricing.py | CostEngine v2 | Historical cost stable after pricing update |
| AC-05 | Unit | test_usage_validator.py | UsageValidator | All 4 commands exit 0 on clean data |
| AC-06 | Performance | test_transcript_performance.py | Reader + Engine | 10k < 30s, incremental < 1s |
| AC-07 | Stress | test_stress_suite.py | All | 100 convs, 10k, deterministic |

---

## 14. Requirement Traceability Matrix

- FR-01 -> Task 1.1 -> FingerprintEngine -> `fingerprint_engine.py` -> `test_fingerprint_engine.py` -> AC-01, AC-02
- FR-02 -> Task 1.2 -> NormalizedUsageRecord v2 -> `connectors/base.py` -> `test_normalization.py` -> AC-03
- FR-03 -> Task 1.3 -> ITranscriptParser + 4 connectors -> `connectors/*.py` -> `test_connectors.py`
- FR-04 -> Task 1.2 -> NormalizedUsageRecord v2 -> `connectors/base.py` -> `test_normalization.py`
- FR-05 -> Task 2.3 -> transcript_offset storage -> `db.py` + `connectors/base.py` -> `test_normalization.py`
- FR-06 -> Task 1.5 -> IncrementalTranscriptReader -> `transcript_engine.py` -> `test_transcript_engine.py`
- FR-07 -> Task 2.1 -> ReconciliationEngine -> `reconciliation_engine.py` -> `test_reconciliation_engine.py` -> AC-05
- FR-08 -> Task 2.2 -> CostEngine v2 -> `cost_engine.py` + `pricing.json` -> `test_versioned_pricing.py` -> AC-04
- FR-09 -> Task 3.2 -> AccuracyBadge CSS -> `webview.html` -> visual test
- FR-10 -> Task 3.3 -> Dashboard panel -> `webview.html` + `extension.ts` -> `test_transcript_first_pipeline.py` -> AC-03
- FR-11 -> Task 3.1 -> UsageValidator -> `usage_validator.py` -> `test_usage_validator.py` -> AC-05
- FR-12 -> Task 1.1 -> FingerprintEngine.register() -> `fingerprint_engine.py` -> `test_fingerprint_engine.py` -> AC-02
- FR-13 -> Task 3.1 -> UsageValidator.doctor() -> `usage_validator.py` -> `test_usage_validator.py`
- FR-14 -> Task 2.2 -> CostEngine.lock_cost() -> `cost_engine.py` -> `test_versioned_pricing.py` -> AC-04
- NFR-01 -> Task 4.1 -> `test_stress_suite.py` -> AC-01
- NFR-02 -> Tasks 2.3, 4.1 -> batch insert + index -> `test_transcript_performance.py` -> AC-06
- NFR-05 -> Task 1.6 -> FEAT-048 regression suite -> 71 existing tests
- NFR-06 -> Task 4.1 -> `test_stress_suite.py` -> AC-07

---

## 15. File-Level Implementation Contracts

### `skills/workflow-runtime/scripts/fingerprint_engine.py`
- **Purpose**: SHA-256 canonical request identity engine with SQLite dedup.
- **Owner**: Coder (Task 1.1)
- **Inputs**: raw provider payload dict, sqlite3.Connection
- **Outputs**: 64-char hex fingerprint, bool (new vs duplicate)
- **Dependencies**: hashlib, json, sqlite3, db.py (request_fingerprints table)
- **Implementation Notes**: `compute()` must be pure (no DB access). `register()` is the only DB writer. Never raise from `compute()` — return empty string on hash failure, set accuracy_source=estimated.
- **Risk**: SHA-256 unavailable on Python 3.10+ is near-impossible. Wrap in try/except ImportError as defensive measure.

### `skills/workflow-runtime/scripts/reconciliation_engine.py`
- **Purpose**: Aggregate fingerprint stats and produce deterministic ReconciliationReport.
- **Owner**: Coder (Task 2.1)
- **Inputs**: sqlite3.Connection, optional List[transcript_paths]
- **Outputs**: ReconciliationReport (persisted to reconciliation_reports table)
- **Dependencies**: fingerprint_engine, transcript_engine, connector_registry, db.py
- **Implementation Notes**: `sync()` must be idempotent — each call inserts new row (never updates old rows). `confidence = parsed / max(1, parsed+corrupted+missing)`. Do not DELETE old reports (audit trail).
- **Risk**: Growing reconciliation_reports table over time. Add periodic cleanup in future iteration.

### `skills/workflow-runtime/scripts/usage_validator.py`
- **Purpose**: CLI for 4 validation/audit commands. Thin wrapper.
- **Owner**: Coder (Task 3.1)
- **Inputs**: CLI args, sqlite3.Connection
- **Outputs**: JSON stdout, summary stderr
- **Dependencies**: reconciliation_engine, db.py, argparse
- **Implementation Notes**: `doctor()` must never crash — wrap all checks in try/except. `diff()` with non-existent run IDs: return `{"error": "run_id not found"}`, exit 2.
- **Risk**: Low. No new DB writes (read-only except reconcile subcommand).

### `skills/workflow-runtime/scripts/connectors/base.py`
- **Purpose**: Extend NormalizedUsageRecord v2 + define ITranscriptParser ABC.
- **Owner**: Coder (Tasks 1.2, 1.3)
- **Implementation Notes**: ITranscriptParser must NOT inherit from ProviderConnector. New accuracy_source values added to valid set. `tool_tokens` clamped but NOT added to `total_tokens`. `fingerprint` validated as 64-char hex or set to None.
- **Risk**: `__post_init__` change could affect existing tests. Ensure total_tokens computation unchanged.

### `skills/workflow-runtime/scripts/transcript_engine.py`
- **Purpose**: Extend `read_new_lines()` to return `(line_dict, byte_offset)` tuples.
- **Owner**: Coder (Task 1.5)
- **Implementation Notes**: Open in `rb` mode. `offset = f.tell()` before each `f.readline()`. Decode as `line.decode("utf-8").rstrip("\r\n")`. Update all callers in `provider_engine.py`.
- **Risk**: Windows CRLF — `rb` mode gives exact byte offset regardless of line ending. UTF-8 decode with `errors="replace"` for safety.

### `skills/workflow-runtime/scripts/cost_engine.py`
- **Purpose**: Extend with versioned pricing, effective_date lookup, historical lock.
- **Owner**: Coder (Task 2.2)
- **Implementation Notes**: `db_conn` parameter added as optional (None = backward compat mode). `lock_cost()` guard: `WHERE pricing_version IS NULL OR pricing_version = ''`. Versioned lookup via `pricing_versions` table; falls back to current pricing.json on miss.
- **Risk**: db_conn=None default ensures all 71 FEAT-048 tests pass without modification.

### `extensions/visualizer/resources/webview.html`
- **Purpose**: Extend AccuracyBadge CSS + add Reconciliation Report panel.
- **Owner**: Coder (Tasks 3.2, 3.3)
- **Implementation Notes**: Run `node build.js` after every edit. New panel: `<div class="reconciliation-panel collapsible">` inside DiagnosticsPanel. Accuracy % row: flexbox, 3 colored segments summing to 100%. `UPDATE_RECONCILIATION` parsed in existing message switch.
- **Risk**: Must run `node build.js` to sync webviewHtml.ts — checklist item in Task 3.3.

### ADR Assessment
- **ADR-006 REQUIRED** before implementation begins:
  - Decision: SHA-256 field ordering, pre-normalization timing, collision policy.
  - File: `docs/adr/ADR-006_fingerprint_algorithm_selection.md`
- **ADR-007 RECOMMENDED** (not blocking):
  - Decision: Raw payload storage — offset pointer vs BLOB.
  - Required only if transcript immutability cannot be guaranteed in all environments.

## Compatibility Mapping (for validation)
### Summary
Included in [0. Baseline Context & References](#0-baseline-context--references).
### Scope
Included in [1. File-by-File Analysis & Proposed Mutations](#1-file-by-file-analysis--proposed-mutations).
### Technical Design
Included in [3. Complete Class & Module Design](#3-complete-class--module-design).
### Files to Change
Included in [1. File-by-File Analysis & Proposed Mutations](#1-file-by-file-analysis--proposed-mutations) and [15. File-Level Implementation Contracts](#15-file-level-implementation-contracts).
### Implementation Steps
Included in [2. Task Ownership & Roles in Implementation Plan](../plans/FEAT-049_transcript_first_accounting_system_plan.md#2-task-ownership--roles).
### Validation Plan
Included in [13. Complete Test Matrix](#13-complete-test-matrix).
### Rollback Plan
Included in [6.6 Migration & Rollback Strategy](#66-migration--rollback-strategy).
