import ast
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent.parent
    paths = [
        root / "experiments/kaggle_mini_benchmark.ipynb",
        root / "dist/kaggle_kernel/kaggle_mini_benchmark.ipynb",
        root / "dist/kaggle_mini_benchmark/kaggle_mini_benchmark.ipynb",
        root / "dist/kaggle_mini_benchmark_run/kaggle_mini_benchmark.ipynb",
    ]
    raw = [p.read_bytes() for p in paths]
    assert raw[0] == raw[1] == raw[2] == raw[3], "Candidate/run notebook copies are not byte-identical"
    nb = json.loads(raw[0].decode("utf-8"))
    code = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    assert len(code) == 10, f"Expected 10 code cells, got {len(code)}"
    for i, cell in enumerate(code):
        ast.parse("".join(cell.get("source", [])), filename=f"candidate-cell-{i}")
        assert cell.get("outputs") == [], f"Cell {i} has saved outputs"
        assert cell.get("execution_count") is None, f"Cell {i} has an execution count"
    first = "".join(code[0].get("source", []))
    whole = "\n".join("".join(c.get("source", [])) for c in code)
    assert "AUTHORIZE_GPU_SMOKE_TEST = False" in first
    assert "AUTHORIZE_GPU_SMOKE_TEST = True" not in whole
    assert whole.index("AUTHORIZE_GPU_SMOKE_TEST = False") < whole.index("import os")
    expected_ids = ["fastapi_15589", "rich_4077", "rich_3944"]
    for task_id in expected_ids:
        assert task_id in whole, f"Missing task ID: {task_id}"
    for placeholder in ("fastapi_task_1", "fastapi_task_2", "requests_task_1"):
        assert placeholder not in whole, f"Placeholder task ID remains: {placeholder}"
    assert "task_ids=TARGET_TASK_IDS" in whole
    for required in ("max_time_minutes=5", "max_tool_calls=28", "max_turns=200", "timeout_seconds=300",
                     "compaction_interval=15", "token_threshold=14336", "event_retention_size=5"):
        assert required in whole, f"Missing current evaluation setting: {required}"
    assert "No leaderboard artifact" in whole
    assert "submission-final.zip" in whole
    assert "ronak1167/gemma4-optimized-candidate" in whole
    assert "ronak1167/gemma4-baseline-submission" not in whole

    for notebook_path in [*root.glob("dist/**/*.ipynb"), *root.glob("experiments/**/*.ipynb")]:
        candidate = json.loads(notebook_path.read_text(encoding="utf-8"))
        candidate_source = "\n".join("".join(cell.get("source", [])) for cell in candidate.get("cells", []) if cell.get("cell_type") == "code")
        if "AUTHORIZE_GPU_SMOKE_TEST" in candidate_source:
            assert "AUTHORIZE_GPU_SMOKE_TEST = True" not in candidate_source, f"GPU execution gate is OPEN: {notebook_path}"
        assert "assert COMPACTION_COUNT > 0" not in candidate_source, f"Notebook incorrectly requires compaction: {notebook_path}"

    manifest = root / "starter/official/tasks.jsonl"
    records = [json.loads(x) for x in manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {x["instance_id"]: x for x in records}
    expected_repos = {
        "rich_4077": "Textualize/rich",
        "rich_3944": "Textualize/rich",
        "fastapi_15589": "fastapi/fastapi",
    }
    for task_id, repo in expected_repos.items():
        assert task_id in by_id and by_id[task_id].get("repo") == repo
        assert by_id[task_id].get("test_patch"), f"No test patch: {task_id}"

    archive = root / "dist/submission-final.zip"
    archive_hash = sha(archive)
    cell5 = "".join(nb["cells"][5]["source"])
    found = re.search(r'EXPECTED_ZIP_SHA256 = "([0-9a-f]{64})"', cell5)
    assert found and found.group(1) == archive_hash, "Notebook ZIP hash is stale"
    source_map = {
        "agent.yaml": root / "agent/agent.yaml",
        "eval_config.yaml": root / "agent/eval_config.yaml",
        "configs/sampling.yaml": root / "agent/configs/sampling.yaml",
        "prompts/system.md": root / "agent/prompts/system.md",
    }
    for rel, source in source_map.items():
        assert sha(source) in cell5, f"Notebook does not pin current source hash for {rel}"

    final_stage = root / "dist/kaggle_dataset_final"
    expected_final_files = {"dataset-metadata.json", "submission-final.zip", *source_map.keys()}
    actual_final = {p.relative_to(final_stage).as_posix() for p in final_stage.rglob("*") if p.is_file()}
    assert actual_final == expected_final_files, f"Local staging mismatch: {actual_final ^ expected_final_files}"
    upload = root / "dist/kaggle_dataset_optimized_upload"
    assert sorted(p.name for p in upload.iterdir()) == ["dataset-metadata.json", "submission-final.zip"]
    assert (upload / "submission-final.zip").read_bytes() == archive.read_bytes()
    upload_meta = json.loads((upload / "dataset-metadata.json").read_text(encoding="utf-8"))
    assert upload_meta["id"] == "ronak1167/gemma4-optimized-candidate"

    km = json.loads((root / "dist/kaggle_mini_benchmark/kernel-metadata.json").read_text(encoding="utf-8"))
    assert km["id"] == "ronak1167/gemma-4-swe-agent-three-task-retry"
    assert km["is_private"] is True and km["machine_shape"] == "NvidiaL4"
    assert km["dataset_sources"][0] == "ronak1167/gemma4-optimized-candidate"
    assert km["enable_internet"] is False and km["code_file"] == "kaggle_mini_benchmark.ipynb"
    print("[PASS] Four candidate/run notebook copies are byte-identical; execution gate closed")
    print("[PASS] All 10 code cells parse; outputs empty; execution counts null")
    print("[PASS] GPU gate is closed and precedes runtime imports")
    print("[PASS] Three task IDs exist in official manifest and map to expected repos")
    print("[PASS] No placeholder IDs; evaluator is configured for three tasks")
    print("[PASS] Notebook pins current archive and all four source-file hashes")
    print("[PASS] Private dataset upload is flat and contains the exact canonical ZIP")
    print("[PASS] Kernel metadata is private, offline, and L4-configured")
    print(f"Candidate archive SHA-256: {archive_hash}")


if __name__ == "__main__":
    main()
