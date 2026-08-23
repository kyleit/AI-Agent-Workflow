# AIWF Bootstrap Receipt

- **Receipt ID**: `{{bootstrap_receipt_id}}`
- **Command ID**: `{{command_id}}`
- **Wrapper Skill**: `aiwf`
- **Bootstrap Skill**: `initialize-workflow`
- **Bootstrap Mode**: `{{mode}}`
- **Decision**: `{{decision}}`

---

## 1. Environment & Project Resolution
- **Repository Root**: `{{repository_root}}`
- **Root Resolution Method**: `git rev-parse --show-toplevel`
- **Repository Identity**: `{{repository_identity}}`
- **Git Commit**: `{{current_commit}}`
- **Git Branch**: `{{current_branch}}`

---

## 2. State & Identity Validation
- **State Authority**: `.agents/state` (`.agents/.session.json` is DEPRECATED)
- **State Path**: `{{state_path}}`
- **State Loaded**: `{{state_loaded}}`
- **Project ID**: `{{project_id}}`
- **Workflow ID**: `{{workflow_id}}`
- **Workflow Action**: `{{workflow_action}}`
- **Last Checkpoint**: `{{last_checkpoint}}`
- **Checkpoint Validation**: `{{checkpoint_validation}}`
- **Approval Validation**: `{{approval_validation}}`
- **Duplicate Workflow Check**: `{{duplicate_workflow_check}}`
- **Duplicate Orchestrator Check**: `{{duplicate_orchestrator_check}}`

---

## 3. Cryptographic Validation
- **Content Hash**: `{{content_hash}}`
- **Algorithm**: `SHA-256`
- **Read-Only**: `{{read_only}}`
