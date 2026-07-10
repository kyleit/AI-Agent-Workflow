---
feature_id: FEAT-020
title: Multi-Agent Analysis Across All Phases
status: brainstorming
created_at: 2026-07-07
---

# Brainstorming – Multi-Agent Analysis Across All Phases (FEAT-020)

## 1. Problem Statement
The current Orchestrator implementation only supports multi-agent execution during the implementation phase. However, complex software engineering tasks require specialized analysis (e.g., UX, security, performance, database schemas) in earlier phases (brainstorming, planning, design) and review phases (verification, release). 

We need to upgrade the framework to allow temporary, read-only **Multi-Agent Analysis** in all phases, while keeping **Parallel Implementation** (which modifies source code) strictly restricted to the Implementation phase.

---

## 2. Requirements & Architecture

### A. Two Execution Models for the Orchestrator
1. **Model A: Analysis Mode (All Phases)**:
   - Spawns temporary specialist agents (e.g., Security Analyst, Database Analyst) to inspect the workspace.
   - Collecting and merging recommendations into a **single canonical document** (e.g., one plan, one blueprint, one verification report).
   - Analysis agents are strictly read-only and never modify codebase files, git tags, or system state.
2. **Model B: Implementation Mode (Phase 6 Only)**:
   - Spawns implementation agents (e.g., Backend Developer, Frontend Developer).
   - Supports Sequential or Parallel execution based on user approval.
   - Handles file locking, conflict resolution, and workspace modification.

### B. Agent Classifications
- **Analysis Agents**: Product Analyst, UX Analyst, Backend Analyst, Frontend Analyst, Database Analyst, Security Analyst, Infrastructure Analyst, Performance Analyst, Architecture Analyst, QA Analyst, Memory Analyst, Documentation Analyst.
- **Implementation Agents**: Backend Developer, Frontend Developer, Database Developer, Infrastructure Developer, Documentation Writer, Test Writer.
- **Review Agents**: Code Reviewer, Security Reviewer, Performance Reviewer, QA Reviewer.

### C. Runtime State & Cleanup
- A new runtime state file `analysis-agents.json` will track active analysis agents per phase.
- Active analysis agents will also sync to `.session.json` to allow the Visualizer to render them in real time.
- All temporary analysis agents must be automatically cleaned up/deleted when a phase finishes (`workflow_runtime complete`).

### D. Visualizer Dashboard
- Update the Visualizer UI to display current phase, running/completed analysis agents, active implementation agents, execution mode, and parallel groups, clearly distinguishing Analysis vs. Implementation.

---

## 3. Impact Assessment
- **AI_RULES.md**: Needs a new section `17. Multi-Agent Analysis Policy`.
- **workflow_runtime.py**: Needs a new `analysis-agent` subcommand to manage/track/list/clear/merge these agents.
- **Visualizer Extension**: Webview needs styling and logic updates to show the two distinct sections.
- **Skills**: Brainstorming, planning, blueprint, verification, and release skills need instructions updated to allow requesting analysis agents.
- **Tests**: Add test scenarios covering analysis lifecycle, cleanup, and implementation constraint checks.

---

## 4. Next Steps
- Submit this brainstorming document for review.
- Proceed to Planning phase to generate the implementation tasks list.
