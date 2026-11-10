import time
from datetime import datetime
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

KERNEL = "ronak1167/gemma-4-swe-agent-four-task-mini-benchmark"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "version-14-mini-benchmark-output"

def main():
    api = KaggleApi()
    api.authenticate()
    deadline = time.monotonic() + 2 * 60 * 60
    while time.monotonic() < deadline:
        status = api.kernels_status(KERNEL)
        value = str(getattr(status, "status", status))
        print(datetime.now().isoformat(timespec="seconds"), value, flush=True)
        upper = value.upper()
        if "COMPLETE" in upper or "ERROR" in upper or "FAILED" in upper:
            OUT.mkdir(parents=True, exist_ok=True)
            token = None
            downloaded = []
            while True:
                page, token = api.kernels_output(
                    KERNEL, str(OUT), quiet=True, force=True, page_token=token, page_size=100
                )
                downloaded.extend(page or [])
                if not token:
                    break
            print("TERMINAL_STATUS", value, flush=True)
            print("DOWNLOADED_FILES", len(downloaded), flush=True)
            print("OUTPUT_DIR", OUT, flush=True)
            return
        time.sleep(60)
    raise TimeoutError("Kernel did not reach a terminal state within 2 hours.")

if __name__ == "__main__":
    main()
