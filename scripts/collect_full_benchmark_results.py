import json
from pathlib import Path

import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PLAN = json.loads((ROOT / "reports" / "benchmark-shards.json").read_text(encoding="utf-8"))
KERNELS = [
    "ronak1167/gemma-4-swe-agent-full-benchmark-shard-1",
    "ronak1167/gemma-4-swe-agent-full-benchmark-shard-2",
    "ronak1167/gemma-4-swe-agent-full-benchmark-shard-3",
    "ronak1167/gemma-4-swe-agent-full-benchmark-shard-4",
]

def download_kernel_output(api, kernel, out):
    status = api.kernels_status(kernel)
    status_text = str(getattr(status, "status", status)).upper()
    print("KERNEL", kernel, "STATUS", status)
    if "COMPLETE" not in status_text:
        raise RuntimeError(f"{kernel} is not COMPLETE: {status}")
    out.mkdir(parents=True, exist_ok=True)
    token = None
    files = []
    while True:
        page, token = api.kernels_output(
            kernel, str(out), quiet=True, force=True, page_token=token, page_size=100
        )
        files.extend(page or [])
        if not token:
            break
    if not any(p.is_file() for p in out.rglob("*")):
        raise RuntimeError(f"No downloadable outputs for {kernel}")
    print("DOWNLOADED", len(files), "files to", out)

def main():
    assert PLAN["task_count"] == 129 and len(PLAN["shards"]) == 4
    api = KaggleApi()
    api.authenticate()
    all_records = {}
    all_predictions = []
    all_expected = []
    per_shard_reports = []

    for i, shard in enumerate(PLAN["shards"]):
        kernel = KERNELS[i]
        out = ROOT / "reports" / f"full-benchmark-shard-{i+1}-output"
        download_kernel_output(api, kernel, out)

        summaries = list(out.rglob("summary.json"))
        records_files = list(out.rglob("task_results.jsonl"))
        diagnostics = list(out.rglob(f"full_benchmark_shard_{i}_diagnostic.json"))
        parquet_files = list(out.rglob(f"submission_shard_{i}.parquet"))
        assert summaries and records_files and diagnostics and parquet_files, (
            f"Shard {i+1}: missing summary/results/diagnostic/parquet output"
        )
        summary = json.loads(summaries[0].read_text(encoding="utf-8"))
        records = [
            json.loads(line)
            for line in records_files[0].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        expected_ids = shard["task_ids"]
        by_id = {r.get("instance_id"): r for r in records}
        assert len(records) == len(expected_ids), (
            f"Shard {i+1}: expected {len(expected_ids)} task records, got {len(records)}"
        )
        assert len(by_id) == len(records), f"Shard {i+1}: duplicate/missing instance IDs"
        assert set(by_id) == set(expected_ids), f"Shard {i+1}: result IDs differ from shard manifest"
        assert summary.get("total_tasks") == len(expected_ids), (
            f"Shard {i+1}: summary task count mismatch: {summary}"
        )
        diagnostic = json.loads(diagnostics[0].read_text(encoding="utf-8"))
        assert diagnostic.get("task_ids") == expected_ids
        assert diagnostic.get("total_tasks") == len(expected_ids)
        assert diagnostic.get("resolved_tasks") == sum(bool(r.get("resolved")) for r in records)

        pred = pd.read_parquet(parquet_files[0])
        assert list(pred.columns) == ["id", "prediction"]
        assert len(pred) == len(expected_ids)
        assert pred["id"].is_unique and set(pred["id"]) == set(expected_ids)
        assert pred["prediction"].map(lambda x: isinstance(x, str)).all()

        resolved = 0
        failed = 0
        for task_id in expected_ids:
            record = by_id[task_id]
            assert isinstance(record.get("resolved"), bool)
            assert isinstance(record.get("test_exit_code"), int)
            resolved += int(record["resolved"])
            failed += int(not record["resolved"])
            if task_id in all_records:
                raise AssertionError(f"Task evaluated more than once: {task_id}")
            all_records[task_id] = record
        all_predictions.append(pred)
        all_expected.extend(expected_ids)
        per_shard_reports.append({
            "shard": i + 1,
            "kernel": kernel,
            "task_count": len(expected_ids),
            "resolved": resolved,
            "unresolved": failed,
            "resolution_rate": resolved / len(expected_ids),
            "summary": summary,
        })
        print(f"SHARD {i+1}: {resolved}/{len(expected_ids)} resolved; parquet rows verified")

    official_ids = [
        json.loads(line)["instance_id"]
        for line in (ROOT / "starter" / "official" / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(official_ids) == 129 and len(set(official_ids)) == 129
    assert len(all_records) == 129 and set(all_records) == set(official_ids)
    assert len(all_expected) == 129 and len(set(all_expected)) == 129

    combined = pd.concat(all_predictions, ignore_index=True)
    assert combined["id"].is_unique and set(combined["id"]) == set(official_ids)
    order = {task_id: i for i, task_id in enumerate(official_ids)}
    combined["_order"] = combined["id"].map(order)
    combined = combined.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)
    assert combined["id"].tolist() == official_ids

    DIST.mkdir(parents=True, exist_ok=True)
    final_parquet = DIST / "submission.parquet"
    combined.to_parquet(final_parquet, index=False)
    readback = pd.read_parquet(final_parquet)
    assert list(readback.columns) == ["id", "prediction"]
    assert len(readback) == 129 and readback["id"].is_unique
    assert readback["id"].tolist() == official_ids
    assert readback["prediction"].map(lambda x: isinstance(x, str)).all()

    resolved_total = sum(bool(r["resolved"]) for r in all_records.values())
    report = {
        "benchmark": "Google Gemma 4 Developer Agent Competition",
        "task_count": 129,
        "resolved_tasks": resolved_total,
        "unresolved_tasks": 129 - resolved_total,
        "resolution_rate": resolved_total / 129,
        "shards": per_shard_reports,
        "submission_artifact": str(final_parquet.relative_to(ROOT)),
        "submission_rows": len(readback),
        "submission_columns": list(readback.columns),
        "submission_bytes": final_parquet.stat().st_size,
        "leaderboard_submission_made": False,
    }
    (ROOT / "reports" / "full-benchmark-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    md = [
        "# Full 129-Task Benchmark Results",
        "",
        f"Resolved: **{resolved_total}/129 ({resolved_total/129:.1%})**",
        f"Unresolved: **{129-resolved_total}/129**",
        "",
        "| Shard | Tasks | Resolved | Resolution rate | Kernel |",
        "|---:|---:|---:|---:|---|",
    ]
    for s in per_shard_reports:
        md.append(
            f"| {s['shard']} | {s['task_count']} | {s['resolved']} | "
            f"{s['resolution_rate']:.1%} | {s['kernel']} |"
        )
    md += [
        "",
        f"Generated {final_parquet.relative_to(ROOT)} with 129 rows and columns id, prediction.",
        "",
        "The parquet was read back and validated. No competition leaderboard submission has been made.",
    ]
    (ROOT / "reports" / "full-benchmark-results.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print("[PASS] All 129 task results are unique, complete, and aligned to the official manifest.")
    print("[PASS] Final submission.parquet has 129 rows and passed read-back validation.")

if __name__ == "__main__":
    main()
