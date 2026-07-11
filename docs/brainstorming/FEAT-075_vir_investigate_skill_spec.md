<!-- File path: docs/brainstorming/FEAT-075_vir_investigate_skill_spec.md -->

# FEAT-075 — vir-investigate Cognitive Skill Specification

---

## 1. Specification Frontmatter
- **Feature ID**: `FEAT-075`
- **Title**: vir-investigate Cognitive Skill Specification
- **Category**: Subsystem Layer 1 (Skills)
- **Status**: Proposed

---

## 2. Objective & Problem Statement

### Objective
Create a lightweight, declarative cognitive skill blueprint managing the RCA and contradiction analysis phase.

### Problem Statement
Root cause categorization rules and contradictions resolution are currently hardcoded in Python. Moving these reasoning patterns to an AI Skill allows models to reason on raw evidence payloads dynamically.

---

## 3. Scope & Deliverables

### Scope
- Define the purpose, allowed actions, inputs, outputs, and validation rules for `vir-investigate`.

### Deliverables
- Skill template saved in `.agents/skills/vir-investigate/SKILL.md`.

---

## 4. Architectural Impact & Acceptance Criteria

### Architectural Impact
Aligns RCA analysis with the AIWF Skill ecosystem, delegating classification decisions to LLM context rules rather than hardcoded scripts.

### Acceptance Criteria
- Skill specification defines exact required inputs (`evidence`) and expected outputs (`RootCause`).
- No Python code resides within the skill definition document.
