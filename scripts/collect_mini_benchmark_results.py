import json
import shutil
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


KERNEL = "ronak1167/gemma-4-swe-agent-four-task-mini-benchmark"
EXPECTED = ["rich_4077", "rich_3944", "fastapi_15589", "requests_7502"]


def main():
    root = Path(__file__).resolve().parent.parent
    out = root / "reports" / "version-3-mini-benchmark-output"
    out.mkdir(parents=True, exist_ok=True)
    api = KaggleApi()
    api.authenticate()
    status = api.kernels_status(KERNEL)
    print("KERNEL_STATUS", status)
    status_text = str(getattr(status, "status", status)).upper()
    if "COMPLETE" not in status_text and "ERROR" not in status_text and "FAILED" not in status_text:
        raise RuntimeError(f"Kernel is not terminal yet: {status}")

    token = None
    all_files = []
    while True:
        files, token = api.kernels_output(
            KERNEL, str(out), quiet=True, force=True, page_token=token, page_size=100
        )
        all_files.extend(files or [])
        if not token:
            break
    print("DOWNLOADED_OUTPUT_FILES", all_files)
    if not any(p.is_file() for p in out.rglob("*")):
        raise RuntimeError("Kaggle kernel has no downloadable output files")

    # Kaggle may preserve the notebook output directory structure or flatten it.
    summary_candidates = list(out.rglob("summary.json"))
    records_candidates = list(out.rglob("task_results.jsonl"))
    assert summary_candidates and records_candidates, "Missing evaluator summary or task_results.jsonl"
    summary = json.loads(summary_candidates[0].read_text(encoding="utf-8"))
    records = [
        json.loads(x)
        for x in records_candidates[0].read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    by_id = {x.get("instance_id"): x for x in records}
    assert len(records) == len(EXPECTED), f"Expected 4 records, got {len(records)}"
    assert set(by_id) == set(EXPECTED), f"Unexpected task IDs: {sorted(by_id)}"
    assert summary.get("total_tasks") == 4
    diagnostic_candidates = list(out.rglob("mini_benchmark_diagnostic.json"))
    assert diagnostic_candidates, "Missing notebook diagnostic summary"
    diagnostic = json.loads(diagnostic_candidates[0].read_text(encoding="utf-8"))
    assert diagnostic.get("task_ids") == EXPECTED
    assert diagnostic.get("total_tasks") == 4
    assert diagnostic.get("resolved_tasks") == sum(bool(x.get("resolved")) for x in records)

    print("TASK RESULTS")
    for task_id in EXPECTED:
        r = by_id[task_id]
        assert isinstance(r.get("resolved"), bool)
        assert isinstance(r.get("test_exit_code"), int)
        patch_candidates = list(out.rglob(f"{task_id}.patch"))
        log_candidates = list(out.rglob(f"{task_id}.log"))
        trace_candidates = list(out.rglob(f"*{task_id}*.json"))
        print(
            task_id,
            "resolved=", r["resolved"],
            "test_exit=", r["test_exit_code"],
            "duration=", r.get("duration_seconds"),
            "tool_calls=", r.get("tool_calls"),
            "patch_file=", bool(patch_candidates),
            "test_log=", bool(log_candidates),
            "trace=", bool(trace_candidates),
            "error=", r.get("error"),
        )
        if r["resolved"]:
            assert r["test_exit_code"] == 0, f"Resolved task has nonzero test exit: {task_id}"
            assert patch_candidates and patch_candidates[0].stat().st_size > 0
    parquet = list(out.rglob("*.parquet"))
    assert not parquet, f"Unexpected leaderboard parquet in diagnostic run: {parquet}"

    resolved = sum(bool(x.get("resolved")) for x in records)
    md = [
        "# Four-Task Mini-Benchmark Results",
        "",
        f"Kernel: {KERNEL}",
        f"Status: {status}",
        f"Resolved: {resolved}/4 ({resolved/4:.0%})",
        "",
        "| Task | Repository | Resolved | Test exit | Duration (s) | Tool calls | Error |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    repos = {
        "rich_4077": "Rich",
        "rich_3944": "Rich",
        "fastapi_15589": "FastAPI",
        "requests_7502": "Requests",
    }
    for task_id in EXPECTED:
        r = by_id[task_id]
        err = str(r.get("error") or "").replace("|", "/").replace("\n", " ")
        md.append(
            f"| {task_id} | {repos[task_id]} | {r['resolved']} | {r['test_exit_code']} | "
            f"{r.get('duration_seconds', 0):.1f} | {r.get('tool_calls', 0)} | {err} |"
        )
    md += ["", "No leaderboard parquet was produced by this diagnostic notebook."]
    (root / "reports" / "mini-benchmark-results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("[PASS] Four-task result records and aggregate validated.")
    print("[PASS] No leaderboard parquet produced.")
    print("RESULT_REPORT", root / "reports" / "mini-benchmark-results.md")


if __name__ == "__main__":
    main()
