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
  usage: none---

# Skill: Project RAG Search (Script-First)

## Purpose
Provide semantic retrieval of Project Memory in response to a natural language query.

## Script Invocation
Execute the Python CLI command:
```bash
aiwf rag search search "<query>"
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
