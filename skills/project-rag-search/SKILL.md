---
name: project-rag-search
command: memory-search
aliases:
  - search
  - rag
category: memory
tags:
  - search
  - rag
  - retrieval
version: 2.5.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Provide fast semantic retrieval of project knowledge for all AI Skills. Script-First Architecture.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: none
  memory: cached
  rag: required
  workspace_scan: none
  environment: none
  version: none
  provider: optional
  usage: none
---

# Skill: Project RAG Search (Script-First)

## Purpose
Provide semantic retrieval of Project Memory in response to a natural language query.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill interfaces with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "optional"` before taking any action.
- **Progress Tracking**: Update status and log progress using `workflow_runtime.py` when integrated in a workflow session.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill strictly adheres to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.

---

## Script Invocation
Execute the Python CLI command:
```bash
python3 .agents/runtime/scripts/project_memory/cli.py search "<query>"
```

## Expected Output
The script returns a structured JSON payload:
```json
{
  "status": "success | failure",
  "query": "...",
  "retrieval_level": "Level 2 — Vector Search | Level 1 — Local Keyword Match",
  "results_count": 0,
  "results": [
    {
      "file": "...",
      "text": "...",
      "score": 0.0
    }
  ]
}
```

## Boundary Rules
- DO NOT perform local text searching or keyword extraction inside the prompt.
- DO NOT call external vector databases directly.
- Let the Python script handle all retrieval steps.
- Present the returned JSON matches as a clean summary.
