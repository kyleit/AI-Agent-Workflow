# Program D Architecture – Plugin & Marketplace Platform

## 1. Vision & Responsibilities
Cung cấp cổng nạp nóng dynamic plugin, client marketplace và kết nối Model Context Protocol (MCP).

## 2. Scope & Out of Scope
- **Scope**: Zip signature check, hot-reload, MCP client setup.
- **Out of Scope**: Financial payment systems.

## 3. Topologies (Runtime, Component, Service, Deployment)
- **Runtime Topology**: ClassLoader registers new modules dynamically.
- **Component Topology**: `MarketplaceClient` ──> `MCPConnector` ──> `PluginRegistry`.
- **Service Topology**: Verification service, Hot-reload service.
- **Deployment Topology**: Plugins running inside isolated micro-VMs or subprocesses.

## 4. Execution Flow & Lifecycle
`VERIFY` -> `LOAD` -> `EXECUTE` -> `UNLOAD`.

## 5. Interface & APIs
- `load_plugin(path: str) -> bool`
- `mcp_call_tool(tool: str, params: dict) -> dict`

## 6. Storage & Concurrency
- **Storage Model**: Local ZIP catalog and metadata database.
- **Concurrency & Consistency**: Concurrent plugin executions sandboxed independently.

## 7. Fault Tolerance & Security
- **Fault Tolerance**: Automatic plugin unloading if resources leak.
- **Security**: Cryptographic verification of author signatures.

## 8. Observability & Risks
- **Observability**: Telemetry charts CPU/RAM of each plugin.
- **Risks**: Malicious plugin. Mitigated by strict sandbox isolation.
