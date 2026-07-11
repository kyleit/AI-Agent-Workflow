<!-- File path: docs/adr/ADR-008_python_protocols_adapter_interfaces.md -->

# ADR-008: Structural Subtyping using Python Protocols for Adapter Interfaces

## Status
Accepted

## Related Feature
[FEAT-057: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts](file:///e:/AgentsProject/docs/brainstorming/FEAT-057_vir_adapter_architecture_and_provider_contracts.md)

## Context
VIR must remain strictly provider-agnostic. Browser automation, storage, VLMs, memory, and state inspection must be decoupled from concrete libraries like Playwright, SQLite, or Qdrant. To enforce this boundary, the core runtime must consume capabilities only through defined adapter interfaces.
In Python, interface enforcement is traditionally done using Abstract Base Classes (ABCs) from the standard `abc` module. However, ABCs enforce strict nominal subtyping (subclasses must explicitly inherit from the ABC), creating tight structural coupling, making it harder to wrap third-party classes, and complicating local mock implementations.

## Decision
We will use **Python Protocols (PEP 544)** to define all adapter interfaces:
- Interfaces will be written as Protocol classes in `vir_runtime/adapters/base/`.
- Concrete implementations (e.g. PlaywrightBrowserAdapter) will satisfy the interface implicitly via duck typing, without needing nominal inheritance.
- Type checking will be verified statically using `mypy`.
- A runtime capability check using `isinstance` or dynamic attribute checking will validate registered adapters at application startup inside the `AdapterRegistry`.

## Alternatives Considered
- **Option A: Nominal inheritance (Abstract Base Classes - ABC):** Concrete adapters inherit from BaseAdapter. Rejected because nominal subclassing is verbose, requires importing core interfaces inside third-party plugins, and complicates wrapping external libraries.
- **Option B: Dynamic reflection mapping:** Runtime inspection of functions without any static type declarations. Rejected because it lacks compile-time safety and prevents IDE autocomplete.

## Trade-offs
### Pros:
- **Maximum Decoupling:** Core runtime never needs to import concrete subclasses; third-party packages can satisfy the adapter protocol without depending directly on VIR code.
- **Easy Mocking:** Writing clean, lightweight mock and stub adapters for unit tests is trivial since no nominal base imports are required.
- **Modern Typing:** Aligns with modern Python typings (PEP 544).

### Cons:
- **Mypy Dependency:** Static safety guarantees require running a static type checker (like mypy) in CI.
- **Runtime validation overhead:** Runtime Protocol validation is slightly more complex than nominal subclass checks, though only executed once during initialization.

## Consequences
- All adapters must be statically type-checked.
- Core code must never import concrete implementations from modules like `playwright` or `qdrant`.
- Third-party plugins can extend VIR simply by conforming to the Protocol signature.

## Risks
- **Runtime interface mismatch:** A plugin changes its signature but passes startup loading checks. *Mitigation:* The Adapter Registry validates method signatures via reflection at startup.

## References
- [VIR Index](file:///e:/AgentsProject/docs/brainstorming/VIR_ARCHITECTURE_BIBLE_INDEX.md)
- [FEAT-057](file:///e:/AgentsProject/docs/brainstorming/FEAT-057_vir_adapter_architecture_and_provider_contracts.md)
