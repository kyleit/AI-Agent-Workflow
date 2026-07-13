# Runtime Recovery Playbook

Step-by-step diagnosis and recovery procedures for AIWF runtime failures.
Each entry follows the pattern: **Symptom → Diagnosis → Fix → Verification**.

---

## 1. Stale File Locks (FileLockConflict)

### Symptom
```
FileLockConflict: Cannot acquire lock for Task X.Y — file src/module.py locked by pid 12345
```

### Diagnosis
```bash
# Show current locks
python3 skills/workflow-runtime/scripts/workflow_runtime.py state --category runtime | jq '.file_locks'

# Check if locking PID is alive
kill -0 12345 2>/dev/null && echo "Alive" || echo "STALE"
```

### Fix
```bash
# Auto-clear stale locks (LockManager clears on next acquire attempt)
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from lock_manager import LockManager
lm = LockManager('.')
stale = [l for l in lm.get_active_locks() if lm.is_stale(l)]
for lock in stale:
    task_id = lock['task_id']
    lm.release(task_id)
    print(f'Cleared stale lock: {lock[\"file_path\"]} (task={task_id})')
print(f'Total locks remaining: {lm.get_lock_count()}')
"
```

### Verification
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from lock_manager import LockManager
lm = LockManager('.')
assert lm.get_lock_count() == 0, 'Locks remain!'
print('OK — No active locks')
"
```

---

## 2. Orphan Workers (WorkerOrphan)

### Symptom
```
WorkerOrphan: Worker w-abc123 (pid 99999) registered but PID not alive
```
Or: Dashboard shows `active_worker_count > 0` but no tasks are running.

### Diagnosis
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from worker_manager import WorkerManager
wm = WorkerManager('.')
orphans = wm.detect_orphans()
print(f'Orphan workers: {orphans}')
for wid in orphans:
    w = wm.get_worker(wid)
    print(f'  {wid}: task={w[\"task_id\"]}, pid={w[\"pid\"]}')
"
```

### Fix
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from worker_manager import WorkerManager
wm = WorkerManager('.')
orphans = wm.detect_orphans()
for wid in orphans:
    wm.terminate_orphan(wid)
    print(f'Terminated orphan: {wid}')
removed = wm.cleanup_completed(keep_failed=True)
print(f'Cleaned up {removed} completed workers')
"
```

### Verification
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from worker_manager import WorkerManager
wm = WorkerManager('.')
assert not wm.has_active_workers(), 'Active workers remain!'
print('OK — No active workers')
"
```

---

## 3. Corrupted JSON State File

### Symptom
```
dashboard._health = "degraded"
dashboard._errors = ["Cannot read/parse workflow state (.agents/state/workflow/workflow.json): ..."]
```

### Diagnosis
```bash
# Identify which file is corrupt
python3 -c "
import sys, json; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from state_path import ensure_dirs, STATE_SUBDIRS, get_state_file
ensure_dirs('.')
for cat in ['workflow', 'runtime', 'context', 'project', 'recovery']:
    path = get_state_file(cat, '.')
    try:
        with open(path) as f: json.load(f)
    except Exception as e:
        print(f'CORRUPT: {path} — {e}')
    except FileNotFoundError:
        print(f'MISSING (OK): {path}')
"
```

### Fix

**Option A — Rebuild from event log** (recommended if events exist):
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from event_reducer import EventReducer
reducer = EventReducer('.')
reducer.replay_all()
print('State rebuilt from event log')
"
```

**Option B — Reset to empty** (last resort):
```bash
# Backup first
cp .agents/state/workflow/workflow.json .agents/state/workflow/workflow.json.bak

# Reset
echo '{}' > .agents/state/workflow/workflow.json
```

### Verification
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from state_aggregator import StateAggregator
agg = StateAggregator('.')
d = agg.aggregate()
assert d['_health'] != 'degraded', f'Still degraded: {d[\"_errors\"]}'
print(f'OK — Health: {d[\"_health\"]}')
"
```

---

## 4. Premature Release Blocked (EarlyReleaseAttempt)

### Symptom
```
PrematureReleaseError: Release not allowed — 3 conditions failed: [...]
```

### Diagnosis
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from release_gate import ReleaseGate
gate = ReleaseGate('.')
allowed, reason = gate.validate()
print(f'Release allowed: {allowed}')
print(f'Block reason: {reason}')
"
```

### Fix

Follow the AIWF workflow in order:

```
1. Complete all implementation phases (ledger.mark_phase_completed)
2. Run debug-to-verify skill → emit DEBUG_PASSED event
3. Run verify step → emit VERIFY_PASSED event
4. Then attempt release
```

```bash
# Check what's blocking
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from ledger import ImplementationLedger
l = ImplementationLedger('.')
data = l.load()
print('Status:', data.get('implementation_status'))
print('All complete:', data.get('all_phases_complete'))
for p in data.get('phases', []):
    print(f'  Phase {p[\"id\"]}: {p[\"status\"]}')
"
```

### Verification
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from release_gate import ReleaseGate
gate = ReleaseGate('.')
allowed, reason = gate.validate()
assert allowed, f'Still blocked: {reason}'
print('OK — Release gate OPEN')
"
```

---

## 5. Event Log Missing or Empty

### Symptom
```
EventReducer: No events to replay (log empty or missing)
```

### Diagnosis
```bash
ls -la .agents/state/events/
wc -l .agents/state/events/events.jsonl 2>/dev/null || echo "events.jsonl missing"
```

### Fix
```bash
# Re-initialize workflow state with minimum required event
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from event_logger import EventLogger, WORKFLOW_INITIALIZED
logger = EventLogger('.')
eid = logger.emit(WORKFLOW_INITIALIZED, {'feature_id': 'UNKNOWN', 'note': 'Recovery init'})
print(f'Emitted WORKFLOW_INITIALIZED: {eid}')
from event_reducer import EventReducer
EventReducer('.').replay_all()
print('State rebuilt')
"
```

### Verification
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from event_logger import EventLogger
logger = EventLogger('.')
events = logger.read_all()
print(f'OK — {len(events)} events in log')
"
```

---

## 6. DAG Cycle Detected (CyclicDependencyError)

### Symptom
```
CyclicDependencyError: Cycle detected in task dependency graph involving: Task A, Task B
```

### Diagnosis
```bash
python3 -c "
import sys, json; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from dag_planner import DAGPlanner
with open('docs/designs/FEAT-XXX_blueprint.json') as f:
    bp = json.load(f)
planner = DAGPlanner()
errors = planner.validate(bp)
for e in errors:
    print('ERROR:', e)
"
```

### Fix
Edit the blueprint JSON to remove circular dependencies:
```bash
# Find the cycle
python3 -c "
import sys, json; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from dag_planner import DAGPlanner
with open('docs/designs/FEAT-XXX_blueprint.json') as f:
    bp = json.load(f)
planner = DAGPlanner()
dag = planner.build(bp)
for task_id, deps in dag['graph'].items():
    print(f'{task_id}: {deps}')
"
```

### Verification
```bash
python3 -c "
import sys, json; sys.path.insert(0, 'skills/workflow-runtime/scripts')
from dag_planner import DAGPlanner
with open('docs/designs/FEAT-XXX_blueprint.json') as f:
    bp = json.load(f)
planner = DAGPlanner()
errors = planner.validate(bp)
assert len(errors) == 0, f'Blueprint still invalid: {errors}'
print('OK — Blueprint is valid')
"
```

---

## Quick Reference Commands

```bash
# Show full dashboard
python3 skills/workflow-runtime/scripts/workflow_runtime.py state

# Show current lock count
python3 -c "import sys; sys.path.insert(0,'skills/workflow-runtime/scripts'); from lock_manager import LockManager; print(LockManager('.').get_lock_count())"

# Show active workers
python3 -c "import sys; sys.path.insert(0,'skills/workflow-runtime/scripts'); from worker_manager import WorkerManager; print(WorkerManager('.').get_active_workers())"

# Check release gate
python3 -c "import sys; sys.path.insert(0,'skills/workflow-runtime/scripts'); from release_gate import ReleaseGate; ok,reason=ReleaseGate('.').validate(); print(f'Release: {ok} — {reason}')"

# Replay events
python3 -c "import sys; sys.path.insert(0,'skills/workflow-runtime/scripts'); from event_reducer import EventReducer; EventReducer('.').replay_all(); print('Done')"
```
