# ADR-201: AIWF Cloud Architecture Decisions

## Status
Approved

## Context
We need to design the local implementation and mock subsystem for testing and validating the AIWF Cloud control plane, fleet operations, distributed scheduler, tenancy boundaries, API gateways, and regional replication.

## Decisions
- **SSO Authentication**: Mock OAuth2 identity validation with tenant context parsing.
- **Tenancy Boundary**: Separate DB namespaces (SQLite/PostgreSQL schema prefixes) for workspaces.
- **Observability**: Structured JSON logging and mock OpenTelemetry event ingestion.
- **Distributed Scheduler**: Local resource manager with worker health queues and tasks routing based on CPU/RAM metrics.
- **OTA Updates**: Package sign verification using asymmetric cryptography simulation.
