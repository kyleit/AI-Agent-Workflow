# Release Subsystem Guide

This guide explains the module-aware versioning and release system.

---

## Release Modes

The framework supports two release modes configured via `.agents/release.config.json`:

### 1. Single Mode (`"release_mode": "single"`)
Used for projects with a single package/module (e.g. backend-only, library).
- A single version is tracked globally.
- Updates the root `CHANGELOG.md` directly.
- Git tag style is simple: `vX.Y.Z`.

### 2. Module Mode (`"release_mode": "module"`)
Used for monorepos, multi-module repositories (e.g. `backend` + `frontend`), desktop apps, mobile projects, or microservices.
- Tracks versions per module independently.
- Updates each affected module's local `CHANGELOG.md`.
- Generates a Release Summary in the root `CHANGELOG.md`.
- Git tags are prefixed per module: `backend/v1.8.2`, `frontend/v3.1.5`.

---

## Configuration Schema (`release.config.json`)

```json
{
  "release_mode": "module",
  "default_branch": "main",
  "root_changelog": "CHANGELOG.md",
  "modules": [
    {
      "name": "backend",
      "path": "backend",
      "version_files": [
        "VERSION",
        "pyproject.toml"
      ],
      "changelog": "CHANGELOG.md",
      "tag_format": "backend/v{version}"
    },
    {
      "name": "frontend",
      "path": "frontend",
      "version_files": [
        "package.json"
      ],
      "changelog": "CHANGELOG.md",
      "tag_format": "frontend/v{version}"
    }
  ]
}
```

---

## Branch Strategy & Safety Guards

- **Branch Check**: Prior to triggering a release, the system checks the active branch. If not on `main`/`master`, the user is explicitly prompted to approve a merge.
- **No Force Operations**: The framework never uses force flags (`--force`) for git pushes, tags, or merges.
- **Non-Git Fallback**: If Git is unavailable, the release process automatically bypasses Git checkouts/tags/pushes while still updating version files, local changelogs, and generating the Release Summary.
