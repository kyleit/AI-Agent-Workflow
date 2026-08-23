# Makefile — workflow-runtime Quality Gates
# ============================================================
# Conventions:
#   make quality         — run all gates (file-size, typecheck, architecture)
#   make check-file-size — validate Python file line counts
#   make typecheck       — run Pyright strict
#   make architecture    — run Import Linter contracts
# ============================================================

.PHONY: quality check-file-size typecheck architecture help

# Default target
help:
	@echo ""
	@echo "workflow-runtime Quality Gates"
	@echo "================================="
	@echo ""
	@echo "  make quality          Run all quality gates"
	@echo "  make check-file-size  Validate Python file size (max 500 lines)"
	@echo "  make typecheck        Run Pyright in strict mode"
	@echo "  make architecture     Run Import Linter architecture contracts"
	@echo ""

# --- GATE 1: File Size ---
check-file-size:
	@echo ""
	@echo "=== GATE 01: File Size (max 500 physical lines) ==="
	python scripts/check_python_file_lines.py

# --- GATE 2: Pyright Strict ---
typecheck:
	@echo ""
	@echo "=== GATE 02: Pyright Strict Type Safety ==="
	python -m pyright workflow_runtime

# --- GATE 3: Import Linter ---
architecture:
	@echo ""
	@echo "=== GATE 03: Import Linter Architecture Contracts ==="
	lint-imports

# --- ALL GATES ---
quality: check-file-size typecheck architecture
	@echo ""
	@echo "=== Quality Gates Complete ==="
