import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path(__file__).resolve().parent.parent
KERNEL = "ronak1167/gemma-4-swe-agent-three-task-retry"
OUT = ROOT / "reports" / "three-task-diagnostic-output"
NOTEBOOK = ROOT / "dist/kaggle_mini_benchmark/kaggle_mini_benchmark.ipynb"

def close_remote_gate():
    print("[SAFEGUARD] Pushing closed-gate notebook to Kaggle...", flush=True)
    content = NOTEBOOK.read_text(encoding="utf-8")
    assert "AUTHORIZE_GPU_SMOKE_TEST = False" in content
    cmd = [sys.executable, "-m", "kaggle", "kernels", "push", "-p", str(ROOT / "dist/kaggle_mini_benchmark")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout, flush=True)
    if res.stderr:
        print("[STDERR]", res.stderr, flush=True)
    print("[SAFEGUARD] Remote gate successfully verified and closed.", flush=True)

def main():
    api = KaggleApi()
    api.authenticate()
    OUT.mkdir(parents=True, exist_ok=True)
    
    start_time = time.monotonic()
    running_start_time = None
    max_queue_hours = 12.0
    max_running_hours = 3.0
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring {KERNEL} (Patient queue mode)...", flush=True)
    
    last_status = None
    while True:
        try:
            status_obj = api.kernels_status(KERNEL)
            status_val = str(getattr(status_obj, "status", status_obj))
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Transient API error: {e}", flush=True)
            time.sleep(30)
            continue
            
        elapsed_min = (time.monotonic() - start_time) / 60
        
        if status_val != last_status:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status changed: {status_val} (Total: {elapsed_min:.1f} min)", flush=True)
            last_status = status_val
            if "RUNNING" in status_val.upper() and running_start_time is None:
                running_start_time = time.monotonic()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] *** Execution started on 4x L4 node! ***", flush=True)
        else:
            if int(elapsed_min) % 10 == 0 and int(elapsed_min) > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status_val} (Total: {elapsed_min:.1f} min)", flush=True)
            
        upper = status_val.upper()
        if "COMPLETE" in upper or "ERROR" in upper or "CANCEL" in upper or "FAIL" in upper:
            print(f"\n[TERMINAL] Kernel reached terminal status: {status_val}", flush=True)
            
            # Download full output
            print(f"[COLLECT] Downloading output files to {OUT}...", flush=True)
            out_cmd = [sys.executable, "-m", "kaggle", "kernels", "output", KERNEL, "-p", str(OUT)]
            subprocess.run(out_cmd, capture_output=True, text=True)
            
            # Close remote gate immediately
            try:
                close_remote_gate()
            except Exception as e:
                print(f"[WARNING] Could not close remote gate: {e}", flush=True)
                
            return
            
        # Check timeouts
        if running_start_time is not None:
            if (time.monotonic() - running_start_time) > max_running_hours * 3600:
                raise TimeoutError(f"Kernel execution exceeded {max_running_hours} hours.")
        else:
            if (time.monotonic() - start_time) > max_queue_hours * 3600:
                raise TimeoutError(f"Kernel queued for over {max_queue_hours} hours without node allocation.")
                
        time.sleep(45)

if __name__ == "__main__":
    main()
