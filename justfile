# Public repository recipes

# Default: list available recipes
default:
    @just --list

# Check required uv tools
setup:
    @tools="$(uv tool list)" && printf '%s\n' "$tools" | grep -qx -- '- lint_Org_files' || { echo "lint_Org_files must be installed as a uv tool" >&2; exit 1; }

# Check Org file style
check: setup
    @echo "=== Checking Org files ==="
    uv run lint_Org_files -p .

# Auto-fix Org file style issues where possible
fix: setup
    uv run lint_Org_files -p . --fix

# Run all tests
test: check
    @echo "Validating external file interfaces..."
    @python3 tests/test_external_interfaces.py
