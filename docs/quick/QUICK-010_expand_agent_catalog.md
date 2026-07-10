# Specification – Expand the Agent Catalog (QUICK-010)

This specification defines the audit findings and design plan to expand the framework's core agent system into a multi-agent specialist catalog.

## 1. Audit Results

Currently, only 5 core agents exist:
- Planner (`planner.md`)
- Architect (`architect.md`)
- Coder (`coder.md`)
- Reviewer (`reviewer.md`)
- Release Manager (`release-manager.md`)

**Gaps Identified**:
- Lacks specialized sub-agents for distinct disciplines (security, database, UI, DevOps, testing, changelog management).
- Specialist agents are not formally registered or structured in the agent directory.
- The `agent_routing.py` module needs to support loading and validating these new specialist agents properly without flagging them as orphaned.

## 2. Proposed Agent Catalog Design

We will introduce 35 specialist agents organized into 6 category directories or directly under `agents/` and `.agents/agents/` (retaining standard structure):
1. **Discovery**: Product Analyst, Business Analyst, Requirement Analyst, Research Agent, Memory Analyst, RAG Analyst.
2. **Planning**: Dependency Analyst, Risk Analyst, Security Planner, Performance Planner, Test Planner.
3. **Architecture**: Backend Architect, Frontend Architect, Database Architect, API Architect, Infrastructure Architect, Security Architect.
4. **Implementation**: Backend Developer, Frontend Developer, Database Developer, Infrastructure Developer, DevOps Developer, Migration Developer, Documentation Writer, Test Developer.
5. **Review**: Code Reviewer, QA Reviewer, Security Reviewer, Performance Reviewer, Accessibility Reviewer, Architecture Reviewer.
6. **Release**: Version Manager, Release Validator, Package Builder, ChangeLog Manager, Publisher.

### Standard 17-Attribute Agent Schema
Every agent file will start with standard YAML frontmatter containing:
```yaml
name: string
role: string
responsibilities: string
artifact_ownership: string
allowed_reads: list of strings
allowed_writes: list of strings
forbidden_actions: list of strings
input_contract: string
output_contract: string
handoff_target: string
done_criteria: string
can_run_in_parallel: boolean
agent_category: string
phase: string
required_skills: list of strings
required_memory: boolean
required_rag_context: boolean
runtime_requirements: list of strings
```

## 3. Orchestrator Dynamic Agent Selection
The Orchestrator will resolve required specialist agents dynamically based on:
- Technology stack detected in `project-profile.json` (e.g. Node.js -> Frontend Architect / Developer; Python -> Backend Architect / Developer).
- Type of request (e.g. bugfix -> Coder, Reviewer, Bug Analyst; release -> Release Manager, Version Manager, Changelog Manager).

## 4. Verification Plan

### Automated Tests
- Validate that all 35 new specialist agents are parsed correctly.
- Ensure all required 17 schema attributes are present.
- Verify owner/specialist relationships are clean and handoffs do not cycle.
- Run complete test suite and fix any regressions.
