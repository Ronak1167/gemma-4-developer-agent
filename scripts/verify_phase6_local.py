import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
for name in (
    "package_final_submission.py",
    "verify_phase4_optimizations.py",
    "verify_mini_benchmark_notebook.py",
    "verify_full_shard_notebooks.py",
    "verify_competition_submission_notebook.py",
):
    print(f"\n=== {name} ===", flush=True)
    subprocess.run([sys.executable, str(root / "scripts" / name)], cwd=root, check=True)
print("\nALL READ-ONLY PHASE 6 CHECKS PASSED.", flush=True)
