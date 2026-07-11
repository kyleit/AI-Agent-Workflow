# File path: skills/vir-runtime/scripts/vir.py
import sys
import os

# Resolving local package path dynamically to avoid PYTHONPATH dependencies
current_dir = os.path.dirname(os.path.abspath(__file__))
package_parent = current_dir # The package vir_runtime lives under skills/vir-runtime/scripts/
if package_parent not in sys.path:
    sys.path.insert(0, package_parent)

from vir_runtime.core.cli import CLIRunner

def main():
    runner = CLIRunner()
    # Forward system arguments to CLIRunner
    exit_code = runner.main(sys.argv[1:])
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
