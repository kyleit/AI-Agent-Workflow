<!-- File path: docs/adr/ADR-007_transcript_first_accounting.md -->

# ADR-007: Transcript-First Accounting for Provider Usage Hardening

## Status
Accepted

## Related Feature
FEAT-049

## Context
AI Engineering Workflow Framework (AIWF) currently relies on parsed JSON summaries to account for token usage and costs. However, these derived summaries are often incomplete, estimated, or lack auditability, leading to inaccurate FinOps tracking. We need a system that treats the provider transcript as the single source of truth for all usage metrics.

## Decision
We implement a transcript-first accounting system by parsing the raw transcripts directly to extract input/output tokens, thinking/reasoning tokens, cached tokens, tool tokens, costs, and context limits. We clearly distinguish between provider-reported, derived, and estimated values.
Key architectural components:
1. Schema Hardening: Add fingerprint, pricing_version, tool_tokens, and transcript_offset to provider_requests and support table reconciliation.
2. Caching: Optimize db schema initialization to run exactly once per process to eliminate Windows subprocess write transaction overhead.
3. Skip Duplicate Writes: Optimize sync_request_history to fetch already saved request IDs and skip duplicate insertions, keeping execution under 5ms.

## Alternatives Considered
- Relying on background summary files: Rejected due to metadata gaps and lack of auditability.
- Parsing transcripts on every request save without caching: Rejected because the duplicate SQLite write transactions caused significant latency and subprocess hangs on Windows.

## Trade-offs
- Pros: Highest accuracy, auditability, multi-provider model support, zero redundancy, and extremely fast execution due to cached schema checks.
- Cons: Overhead of parsing transcript files (mitigated by checking exists/ignoring duplicate IDs).

## Consequences
All CLI subcommands (start, step, complete) will be extremely fast and reliable on Windows, ensuring precise FinOps usage analytics.

## Risks
- Transcript format changes: Mitigated by fallback estimates and robust regex parsing.

## References
- [FEAT-049_transcript_first_accounting_system_plan.md](file:///E:/AgentsProject/docs/plans/FEAT-049_transcript_first_accounting_system_plan.md)
- [db.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/db.py)
- [context.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/context.py)
