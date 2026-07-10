# Fix Specification: Untrack and Ignore .session.json (FIX-006)

## Problem Statement
The file `.agents/.session.json` is currently tracked in the root Git repository. Because it stores current workflow state, checkpoints, and token usage, it is modified on almost every turn. This leads to:
1. Noisy git changes (dirty working tree) during active development.
2. Complications during releases, as the file is constantly changing.
3. Merge conflicts when working across branches or pulling upstream.

## Proposed Changes

### Root gitignore

#### [MODIFY] [.gitignore](file:///Volumes/Kyle/AgentsProject/.gitignore)
Add `.agents/.session.json` to the ignore list to prevent Git from tracking it in the future.

```diff
 node_modules
 __pycache__/
 *.pyc
 *.db
 *.db-journal
 *.db-wal
 *.tmp
 *.bak
+ .agents/.session.json
```

### Git Index Changes
Untrack the file from git tracking cache using:
```bash
git rm --cached .agents/.session.json
```
This will remove it from git index but preserve the local file on the current machine.

---

## Verification Plan

### Automated Verification
- Verify `git status` shows `.agents/.session.json` as deleted (staged for deletion).
- Verify that running a workflow command (e.g. `workflow_runtime init`) still reads and writes `.agents/.session.json` successfully on the local filesystem.
