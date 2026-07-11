# Skill Specification — vir-memory-update

This skill specifies baselines promotions, database growth maintenance, and vector learning updates.

---

## 1. Metadata Frontmatter
- **Name**: `vir-memory-update`
- **Description**: Promote active baselines, prune expired sessions, and write vector memories.
- **Version**: `1.0.0`

---

## 2. Core Specification

### Purpose
Update active project baselines and compile historical learning patterns.

### Required Inputs
- `session_id`: Unique identifier of active run.
- `outcome`: Consensus and RCA results payload.
- `new_baseline_png`: Screenshot binary bytes array to promote.

### Produced Outputs
- `vector_learning`: Saved learning outcome embeddings.
- `baseline_db_status`: Database write results record.

---

## 3. Invocation & Execution Rules

### Allowed Actions
- Appending new outcomes history files or database records.
- Overwriting existing baselines under explicit promote commands.
- Pruning baselines older than configured expirations.

### Forbidden Actions
- Modifying other workspace skills configs.
- Overwriting active baselines without verification consensus passes.

### Required Runtime APIs
- `vir.runtime.memory.promote_baseline(feature_id, route, viewport, data)`
- `vir.runtime.memory.save_learning(session_id, outcome)`
