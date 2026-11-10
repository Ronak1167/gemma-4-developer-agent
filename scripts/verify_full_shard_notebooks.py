import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = [json.loads(line) for line in (ROOT / "starter/official/tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
TASK_MAP = {task["instance_id"]: task for task in TASKS}
PLAN = json.loads((ROOT / "reports/benchmark-shards.json").read_text(encoding="utf-8"))
ARCHIVE_HASH = hashlib.sha256((ROOT / "dist/submission-final.zip").read_bytes()).hexdigest()
SOURCE_HASHES = {
    "agent.yaml": hashlib.sha256((ROOT / "agent/agent.yaml").read_bytes()).hexdigest(),
    "eval_config.yaml": hashlib.sha256((ROOT / "agent/eval_config.yaml").read_bytes()).hexdigest(),
    "configs/sampling.yaml": hashlib.sha256((ROOT / "agent/configs/sampling.yaml").read_bytes()).hexdigest(),
    "prompts/system.md": hashlib.sha256((ROOT / "agent/prompts/system.md").read_bytes()).hexdigest(),
}


def assignment_value(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing literal assignment: {name}")


assert len(TASKS) == 129 and len({task["instance_id"] for task in TASKS}) == 129
assert PLAN["task_count"] == 129 and PLAN["shard_count"] == 4
seen = []

for shard in PLAN["shards"]:
    index = shard["shard"]
    expected_ids = shard["task_ids"]
    folder = ROOT / "dist" / f"kaggle_full_shard_{index}"
    notebook_path = folder / f"kaggle_full_shard_{index}.ipynb"
    metadata_path = folder / "kernel-metadata.json"
    assert notebook_path.is_file() and metadata_path.is_file(), f"Missing shard {index} artifacts"

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    assert code_cells, f"Shard {index} has no code cells"
    sources = []
    trees = []
    for cell_index, cell in enumerate(code_cells):
        source = "".join(cell.get("source", []))
        tree = ast.parse(source, filename=f"shard-{index}-cell-{cell_index}")
        assert cell.get("execution_count") is None and cell.get("outputs") == [], f"Shard {index} contains saved execution state"
        sources.append(source)
        trees.append(tree)
    code = "\n".join(sources)

    assert "AUTHORIZE_GPU_SMOKE_TEST = False" in sources[0], f"Shard {index} gate missing or not first"
    assert "AUTHORIZE_GPU_SMOKE_TEST = True" not in code, f"Shard {index} GPU gate open"
    assert code.index("AUTHORIZE_GPU_SMOKE_TEST = False") < code.index("import os"), f"Shard {index} gate runs after imports"
    assert "assert COMPACTION_COUNT > 0" not in code, f"Shard {index} still requires compaction"
    for required in ("timeout_seconds=300", "max_tool_calls=28", "max_time_minutes=5", "max_turns=200", "compaction_interval=15", "token_threshold=14336"):
        assert required in code, f"Shard {index} missing current setting: {required}"
    assert ARCHIVE_HASH in code, f"Shard {index} archive hash is stale"
    for rel, digest in SOURCE_HASHES.items():
        assert digest in code, f"Shard {index} source hash is stale: {rel}"

    ids = None
    repos = None
    for tree in trees:
        if ids is None:
            try:
                ids = assignment_value(tree, "TARGET_TASK_IDS")
            except AssertionError:
                pass
        if repos is None:
            try:
                repos = assignment_value(tree, "EXPECTED_REPOS")
            except AssertionError:
                pass
    assert ids == expected_ids, f"Shard {index} task IDs do not match shard manifest"
    expected_repos = {task_id: TASK_MAP[task_id]["repo"] for task_id in expected_ids}
    assert repos == expected_repos, f"Shard {index} repo map mismatch"
    assert len(ids) == shard["task_count"] and all(task_id in TASK_MAP for task_id in ids)
    assert f"FULL_BENCHMARK_SHARD_{index}" in code
    assert f"full_benchmark/shard_{index}" in code
    assert f"submission_shard_{index}.parquet" in code
    seen.extend(ids)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["id"] == f"ronak1167/gemma-4-swe-agent-full-benchmark-shard-{index + 1}"
    assert metadata["is_private"] is True and metadata["enable_gpu"] is True
    assert metadata["enable_internet"] is False and metadata["machine_shape"] == "NvidiaL4"
    assert "ronak1167/gemma4-optimized-candidate" in metadata["dataset_sources"]
    assert "metric/gemma-4-developer-agent-wheelhouse" in metadata["dataset_sources"]
    print(f"[PASS] shard {index + 1}: {len(ids)} exact tasks, current hashes, AST, closed GPU gate, private/offline metadata")

assert len(seen) == 129 and len(set(seen)) == 129 and set(seen) == set(TASK_MAP)
generator = (ROOT / "scripts/prepare_full_benchmark_shards.py").read_text(encoding="utf-8-sig")
assert 'compaction_interval=15' in generator and 'token_threshold=14336' in generator
print("[PASS] all 129 official tasks appear exactly once across four regenerated shard notebooks")
print("[PASS] shard generator is aligned with the official 15/14336 compaction configuration")
