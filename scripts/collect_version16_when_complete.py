import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "ronak1167/gemma-4-swe-agent-four-task-mini-benchmark"
OUT = ROOT / "reports" / "version16-collected"
OUT.mkdir(parents=True, exist_ok=True)
deadline = time.time() + 2 * 60 * 60
last_status = ""

while time.time() < deadline:
    p = subprocess.run([sys.executable, "-m", "kaggle", "kernels", "status", SLUG],
                       capture_output=True, text=True, timeout=90)
    status_text = (p.stdout + "\n" + p.stderr).strip()
    last_status = status_text
    print(status_text, flush=True)
    if "KernelWorkerStatus.COMPLETE" in status_text or "KernelWorkerStatus.ERROR" in status_text:
        pull = subprocess.run([sys.executable, "-m", "kaggle", "kernels", "output", SLUG, "-p", str(OUT)],
                              capture_output=True, text=True, timeout=600)
        print("OUTPUT_PULL\n" + pull.stdout + "\n" + pull.stderr, flush=True)
        diagnostic = OUT / "mini_benchmark_diagnostic.json"
        report = ["# Version 16 Four-Task Diagnostic Collection", "", status_text, ""]
        if diagnostic.is_file():
            data = json.loads(diagnostic.read_text(encoding="utf-8"))
            report += [
                f"Resolved: {data.get('resolved_tasks')}/{data.get('total_tasks')}",
                f"Resolution rate: {data.get('resolution_rate')}",
                f"Context compaction events: {data.get('context_compaction_events')}",
                "",
                "| Task | Repo | Resolved | Test exit | Error |",
                "|---|---|---:|---:|---|",
            ]
            for row in data.get("results", []):
                err = str(row.get("error") or "").replace("|", "/").replace("\n", " ")[:300]
                report.append(f"| {row.get('task_id')} | {row.get('repo')} | {row.get('resolved')} | {row.get('test_exit_code')} | {err} |")
        else:
            report.append("No mini_benchmark_diagnostic.json was present in the downloaded outputs.")
        files = sorted(x.name for x in OUT.iterdir() if x.is_file())
        report += ["", "Downloaded files:", *[f"- {x}" for x in files], ""]
        (ROOT / "reports" / "version16-collection-audit.md").write_text("\n".join(report), encoding="utf-8")
        print("COLLECTION_COMPLETE", flush=True)
        break
    time.sleep(60)
else:
    (ROOT / "reports" / "version16-collection-audit.md").write_text(
        "# Version 16 Collection Timed Out\n\n" + last_status + "\n\nNo result was claimed or fabricated.\n",
        encoding="utf-8")
    print("COLLECTION_DEADLINE_REACHED", flush=True)

