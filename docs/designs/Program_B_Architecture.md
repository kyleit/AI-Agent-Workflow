# Program B Architecture – Cognitive Intelligence Platform

## 1. Vision & Responsibilities
Tối ưu hóa tài nguyên hội thoại, định tuyến model thông minh và triển khai vòng lặp tự sửa lỗi (self-healing).

## 2. Scope & Out of Scope
- **Scope**: Summarization, Token Budget routing, Error healing loop.
- **Out of Scope**: Pre-training LLMs.

## 3. Topologies (Runtime, Component, Service, Deployment)
- **Runtime Topology**: Context filters intercepts prompts before reaching LLM API.
- **Component Topology**: `ContextCompressor` ──> `ModelRouter` ──> `LLM_API`.
- **Service Topology**: Semantic summarizer service, Model router service.
- **Deployment Topology**: Built-in Python library runtime embedded in Executive Loop.

## 4. Execution Flow & Lifecycle
`INTERCEPT` -> `COMPRESS` -> `ROUTE` -> `HEAL` (if error).

## 5. Interface & APIs
- `route_prompt(prompt: str) -> dict`
- `summarize_history(history: list) -> list`

## 6. Storage & Concurrency
- **Storage Model**: Cache prompt local SQLite file.
- **Concurrency & Consistency**: Single-thread non-blocking async parser.

## 7. Fault Tolerance & Security
- **Fault Tolerance**: Fallback to premium model if cheap routed model fails verification.
- **Security**: Prevent system prompt leaking during nén context logs.

## 8. Observability & Risks
- **Observability**: Dashboard displays prompt compression metrics and token usage costs.
- **Risks**: Summary deletes core error stack trace. Mitigated by leaving recent 2k logs untouched.
