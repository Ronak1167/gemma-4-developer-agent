import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_BENCH = ROOT / "dist/kaggle_mini_benchmark"
NOTEBOOK = DIST_BENCH / "kaggle_mini_benchmark.ipynb"
BACKUP = DIST_BENCH / "kaggle_mini_benchmark.ipynb.bak"
KERNEL_SLUG = "ronak1167/gemma-4-swe-agent-three-task-retry"

def main():
    print(f"=== LAUNCHING AUTHORIZED GPU RUN: {KERNEL_SLUG} ===")
    
    # 1. Verify gate is currently closed
    content = NOTEBOOK.read_text(encoding="utf-8")
    assert "AUTHORIZE_GPU_SMOKE_TEST = False" in content, "Pre-condition failed: Gate was not closed"
    
    # 2. Backup safe notebook
    shutil.copyfile(NOTEBOOK, BACKUP)
    
    try:
        # 3. Open execution gate in notebook
        opened_content = content.replace("AUTHORIZE_GPU_SMOKE_TEST = False", "AUTHORIZE_GPU_SMOKE_TEST = True", 1)
        NOTEBOOK.write_text(opened_content, encoding="utf-8")
        print("[GATE] Temporarily opened execution gate for push.")
        
        # 4. Push kernel to Kaggle
        cmd = [sys.executable, "-m", "kaggle", "kernels", "push", "-p", str(DIST_BENCH)]
        print(f"[PUSH] Executing: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print("[STDERR]", res.stderr)
        assert res.returncode == 0, f"Kernel push failed with code {res.returncode}"
        print("[PUSH] Kernel successfully pushed to Kaggle!")
        
    finally:
        # 5. Immediately restore closed gate locally
        shutil.copyfile(BACKUP, NOTEBOOK)
        if BACKUP.exists():
            BACKUP.unlink()
        restored_content = NOTEBOOK.read_text(encoding="utf-8")
        assert "AUTHORIZE_GPU_SMOKE_TEST = False" in restored_content
        print("[GATE] Local execution gate IMMEDIATELY restored to False.")

    # 6. Check initial status
    time.sleep(5)
    status_cmd = [sys.executable, "-m", "kaggle", "kernels", "status", KERNEL_SLUG]
    status_res = subprocess.run(status_cmd, capture_output=True, text=True)
    print("[STATUS]", status_res.stdout.strip())

if __name__ == "__main__":
    main()

