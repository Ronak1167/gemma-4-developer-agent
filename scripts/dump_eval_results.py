import json
from pathlib import Path

base_dir = Path("reports/version-10-smoke-test-output")

# 1. Summary
summary_file = base_dir / "results" / "smoke_test" / "summary.json"
if summary_file.exists():
    print("=== SUMMARY.JSON ===")
    print(summary_file.read_text(encoding="utf-8"))

# 2. Task Results
task_results_file = base_dir / "results" / "smoke_test" / "task_results.jsonl"
if task_results_file.exists():
    print("\n=== TASK_RESULTS.JSONL ===")
    print(task_results_file.read_text(encoding="utf-8"))

# 3. Diagnostic Summary
diag_file = base_dir / "smoke_test_diagnostic.json"
if diag_file.exists():
    print("\n=== SMOKE_TEST_DIAGNOSTIC.JSON ===")
    print(diag_file.read_text(encoding="utf-8"))

