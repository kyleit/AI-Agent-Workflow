# Skill Specification — vir-runtime

This skill specifies how the Visual Intelligence Runtime manages the sandbox target environment lifecycle.

---

## 1. Metadata Frontmatter
- **Name**: `vir-runtime`
- **Description**: Target application lifecycle management, dev server controls, and sandbox environment validation.
- **Version**: `1.0.0`

---

## 2. Core Specification

### Purpose
Automate and supervise target application build and startup phases under deterministic port bounds.

### Responsibilities
- Locate available localhost sockets.
- Execute dev/build shell commands in sub-processes.
- Clean process trees on session termination.

### Required Inputs
- `dev_command`: Command string to launch development server (e.g. `npm run dev`).
- `build_command`: Optional build process command.
- `startup_timeout_seconds`: Timeout limit for HTTP port probes.

### Produced Outputs
- `port`: Allocated active TCP port.
- `pid`: Process group identifier of target dev server.

---

## 3. Invocation & Execution Rules

### Allowed Actions
- Query local open sockets using socket binds.
- Spawning background processes under standard shell wrappers.
- Recursively calling Win32 API process tree terminators.

### Forbidden Actions
- Modifying target application source files.
- Communicating with external networks (only local loops are permitted).
- Spawning processes that bypass parent tracking constraints.

### Required Runtime APIs
- `vir.runtime.ports.find_available_port()`
- `vir.runtime.process.terminate_tree(pid)`
