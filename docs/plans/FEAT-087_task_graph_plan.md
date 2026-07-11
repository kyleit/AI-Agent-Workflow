# Implementation Plan – FEAT-087: Task Graph Engine

## 1. Goal & Objectives
Implement a topological-sorting Directed Acyclic Graph (DAG) task engine to schedule tasks based on priorities and resolve dependencies dynamically.

## 2. Sprint & Milestones
- **Sprint**: Sprint 1 (Minimum Viable Runtime)
- **Milestone**: M1 (Core Kernel Execution)
- **Target Date**: Week 1

## 3. Deliverables
- `dag.py`: Kahn's algorithm cycle checker, topological scheduler.
- `priority_queue.py`: Task priority queue.
- `breakdown_engine.py` updates to output standard DAG nodes.

## 4. Dependencies
- FEAT-086: Executive Loop Controller.

## 5. Risks & Mitigations
- **Risk**: Circular dependencies generated dynamically at runtime.
- **Mitigation**: Run `has_cycle()` validation after every dynamic graph modification.

## 6. Definition of Done (DoD)
- Compile task structures into an acyclic graph.
- Successfully schedule non-dependent tasks in priority order.

## 7. Test Strategy
- Unit tests: verify topological sort outcomes on various DAG schemas.
- Cycle tests: verify that cyclical definitions are rejected with descriptive compile errors.

## 8. Release Gate
- Code builds cleanly; cycle detection tests pass.
