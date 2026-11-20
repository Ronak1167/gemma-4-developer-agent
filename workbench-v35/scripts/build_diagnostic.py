from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dist" / "kaggle_v31_diagnostic" / "kaggle_mini_benchmark.ipynb"
SOURCE_META = ROOT / "dist" / "kaggle_v31_diagnostic" / "kernel-metadata.json"
OUT = ROOT / "dist" / "kaggle_v35_diagnostic"
AGENT = ROOT / "workbench-v35" / "agent"
ARCHIVE = ROOT / "dist" / "submission-v35.zip"
DATASET = ROOT / "dist" / "kaggle_v35_candidate_dataset"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
TASK_MANIFEST = ROOT / "starter" / "official" / "tasks.jsonl"
TARGET_TASKS = {
    "fastapi_14458": "fastapi/fastapi",
    "rich_4075": "Textualize/rich",
    "requests_7309": "psf/requests",
    "httpx_3672": "encode/httpx",
}
FILES = (
    "agent.yaml",
    "eval_config.yaml",
    "configs/sampling.yaml",
    "prompts/system.md",
    "sub_agents/code_analyzer.yaml",
    "sub_agents/analyzer.md",
    "skills/public_issue_memory/SKILL.md",
    "skills/public_issue_memory/scripts/search.py",
    "skills/public_issue_memory/assets/index.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for required in (SOURCE, SOURCE_META, ARCHIVE, DATASET / "dataset-metadata.json", TASK_MANIFEST):
        if not required.is_file():
            raise SystemExit(f"Missing v35 diagnostic input: {required}")

    manifest = [json.loads(line) for line in TASK_MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {item["instance_id"]: item for item in manifest}
    if len(by_id) != len(manifest):
        raise SystemExit("Duplicate task IDs in the official public manifest.")
    for task_id, expected_repo in TARGET_TASKS.items():
        item = by_id.get(task_id)
        if item is None:
            raise SystemExit(f"Held-out task ID is absent from the official manifest: {task_id}")
        if item.get("repo") != expected_repo:
            raise SystemExit(f"Repository mismatch for {task_id}: {item.get('repo')} != {expected_repo}")
        if not item.get("test_patch"):
            raise SystemExit(f"Official hidden test patch is missing for held-out task: {task_id}")
    if len(TARGET_TASKS) != 4 or len(set(TARGET_TASKS)) != 4:
        raise SystemExit("Diagnostic task selection must contain four unique tasks.")

    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    if len(cells) != 11:
        raise SystemExit(f"Unexpected source notebook structure: {len(cells)}")

    def get(index: int) -> str:
        return "".join(cells[index].get("source", []))

    def set_cell(index: int, source: str) -> None:
        cells[index]["source"] = source.splitlines(keepends=True)
        cells[index]["outputs"] = []
        cells[index]["execution_count"] = None

    set_cell(0, """# Gemma 4 Developer Agent — v35 Retrieval-Augmented Generalization Diagnostic

Private diagnostic only. This notebook evaluates the exact v35 archive, including the read-only BM25 public-issue retrieval skill and optional read-only code analyzer, on four held-out public development tasks (one per repository).

Tasks: fastapi_14458, rich_4075, requests_7309, httpx_3672.

Candidate: Gemma 4 31B; 4096 output tokens; 1024 thinking tokens; 300-second command timeout; 40 tool calls; 5 minutes per task; 500 turns. Use the harness-standard context compaction settings: threshold 14336, interval 15, overlap 2, retain 5 events.

The GPU execution gate is CLOSED by default. This notebook is diagnostic-only. It never creates or uploads a leaderboard submission.
""")

    cell5 = get(5)
    cell5 = cell5.replace('EXPECTED_ZIP_SHA256 = "58ffbf273460c22c2ecb3f2b309bc96c8da14c577a35762d59afb86a19e45850"', f'EXPECTED_ZIP_SHA256 = "{sha(ARCHIVE)}"')
    hash_map = "EXPECTED_FILE_HASHES = {\n" + "".join(
        f'    "{name}": "{sha(AGENT / name)}",\n' for name in FILES
    ) + "}"
    cell5, count = re.subn(r"EXPECTED_FILE_HASHES = \{.*?\n\}", hash_map, cell5, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Could not safely replace the diagnostic candidate hash manifest.")

    cell5 = cell5.replace("gemma4-v31-candidate", "gemma4-v35-candidate")
    cell5 = cell5.replace("submission-v31.zip", "submission-v35.zip")
    cell5 = cell5.replace("submission-v31", "submission-v35")
    cell5 = cell5.replace("submission_v31", "submission_v35")
    cell5 = cell5.replace("kaggle_v31_candidate_dataset", "kaggle_v35_candidate_dataset")
    cell5 = cell5.replace("v31", "v35")

    matcher = re.compile(
        r"    def is_complete_candidate\(directory: Path\) -> bool:\n.*?(?=\n    MOUNTED_DIR)",
        re.S,
    )
    replacement = (
        "    def is_complete_candidate(directory: Path) -> bool:\n"
        "        return all((directory / Path(rel_path)).is_file() for rel_path in EXPECTED_FILE_HASHES)"
    )
    cell5, count = matcher.subn(replacement, cell5, count=1)
    if count != 1:
        raise SystemExit("Could not update candidate completeness check for the v35 skill/sub-agent files.")
    set_cell(5, cell5)

    cell6 = get(6)
    set_cell(6, cell6.replace("v31", "v35"))

    cell7 = get(7)
    if f'MODEL_NAME = "{MODEL}"' not in cell7:
        raise SystemExit("Diagnostic source does not explicitly configure the 31B model.")
    set_cell(7, cell7.replace("v31", "v35"))

    cell8 = get(8)
    cell8 = cell8.replace('Path("/kaggle/working/results/v31_heldout")', 'Path("/kaggle/working/results/v35_heldout")')
    cell8 = cell8.replace("timeout_seconds=120,", "timeout_seconds=300,")
    cell8 = cell8.replace("max_time_minutes=5,", "max_time_minutes=5,")
    cell8 = cell8.replace("max_tool_calls=40,", "max_tool_calls=40,")
    cell8 = cell8.replace("max_turns=120,", "max_turns=500,")
    cell8 = cell8.replace("compaction_interval=5,", "compaction_interval=15,")
    cell8 = cell8.replace("token_threshold=8192,", "token_threshold=14336,")
    cell8 = cell8.replace("event_retention_size=3,", "event_retention_size=5,")
    cell8 = cell8.replace("v31", "v35")
    set_cell(8, cell8)

    cell9 = get(9).replace("v31", "v35")
    set_cell(9, cell9)

    cell10 = get(10)
    cell10 = cell10.replace("V31_FOUR_REPOSITORY_HELDOUT_GENERALIZATION", "V35_FOUR_REPOSITORY_RETRIEVAL_AND_GENERALIZATION")
    cell10 = cell10.replace("v31_heldout", "v35_heldout")
    cell10 = cell10.replace("v31", "v35")
    cell10 = cell10.replace('"timeout_seconds": 90', '"timeout_seconds": 300')
    cell10 = cell10.replace('"max_time_minutes": 5', '"max_time_minutes": 5')
    cell10 = cell10.replace('"max_tool_calls": 28', '"max_tool_calls": 40')
    cell10 = cell10.replace('"max_turns": 80', '"max_turns": 500')
    cell10 = cell10.replace('"token_threshold": 8192', '"token_threshold": 14336')
    cell10 = cell10.replace('"compaction_interval": 5', '"compaction_interval": 15')
    cell10 = cell10.replace('"event_retention_size": 3', '"event_retention_size": 5')
    for key, value in (("timeout_seconds", 300), ("max_time_minutes", 5), ("max_tool_calls", 40), ("max_turns", 500)):
        cell10 = re.sub(rf'("{key}"\s*:\s*)\d+', rf'\g<1>{value}', cell10)
    set_cell(10, cell10)

    # Preserve partial results even when model startup, one task, or the evaluator fails.
    set_cell(8, r"""# 7. Run Selected Tasks Through the Official SWE-Gemma Evaluator API
import asyncio
import concurrent.futures
import traceback
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import EventsCompactionConfig
from swegemma.config import EvalConfig, build_submission_limits
from swegemma.evaluate import Evaluator

def run_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)

import io
import logging
COMPACTION_LOG_BUFFER = io.StringIO()
COMPACTION_LOGGER = logging.getLogger("google_adk.google.adk.apps.compaction")
COMPACTION_PREVIOUS_LEVEL = COMPACTION_LOGGER.level
COMPACTION_HANDLER = logging.StreamHandler(COMPACTION_LOG_BUFFER)
COMPACTION_LOGGER.setLevel(logging.DEBUG)
COMPACTION_LOGGER.addHandler(COMPACTION_HANDLER)
EVALUATION_ERROR = None
eval_result = None
RESULTS_DIR = Path("/kaggle/working/results/v35_heldout")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

try:
    limits, generation_constraints = build_submission_limits()
    eval_config = EvalConfig(
        tasks_path=tasks_file,
        snapshots_dir=snapshots_dir,
        results_dir=RESULTS_DIR,
        submission_dir=SUBMISSION_DIR,
        models=models,
        sandbox="subprocess",
        timeout_seconds=300,
        verification_timeout_seconds=300,
        max_time_minutes=5,
        max_tool_calls=40,
        max_turns=500,
        task_ids=TARGET_TASK_IDS,
        limits=limits,
        generation_constraints=generation_constraints,
        adapter_manifest=adapters,
        context_cache_config=ContextCacheConfig(
            min_tokens=2048,
            ttl_seconds=1800,
            cache_intervals=10,
        ),
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=15,
            overlap_size=2,
            token_threshold=14336,
            event_retention_size=5,
        ),
        graph_dir=str(graphs_dir),
        embeddings_dir=str(embeddings_dir),
        wheels_dir=wheels_dir,
        concurrency=1,
        verbose=False,
        display_mode="quiet",
    )
    evaluator = Evaluator(eval_config)
    eval_result = run_sync(evaluator.run())
except Exception as exc:
    EVALUATION_ERROR = f"{type(exc).__name__}: {exc}"
    (Path("/kaggle/working") / "v35_evaluation_exception.txt").write_text(
        traceback.format_exc(), encoding="utf-8"
    )
    print(f"[EVALUATION ERROR] {EVALUATION_ERROR}")
    traceback.print_exc()
finally:
    COMPACTION_LOGGER.removeHandler(COMPACTION_HANDLER)
    COMPACTION_LOGGER.setLevel(COMPACTION_PREVIOUS_LEVEL)
    srv = globals().get("server_instance") or locals().get("server_instance")
    if srv is not None:
        try:
            srv.stop()
            print("[CLEANUP] vLLM server stopped.")
        except Exception as e:
            print(f"[CLEANUP ERROR] Error stopping vLLM server: {e}")

COMPACTION_LOG_TEXT = COMPACTION_LOG_BUFFER.getvalue()
COMPACTION_COUNT = COMPACTION_LOG_TEXT.count("Token-threshold event compactor finished")
print(f"[CONTEXT] Token-threshold compaction events observed: {COMPACTION_COUNT}")
if eval_result is not None:
    print(f"[EVALUATOR] Returned {len(eval_result.task_results)} of {len(TARGET_TASK_IDS)} requested task records.")
    for task_result in eval_result.task_results:
        print(
            f"Task: {task_result.instance_id} | Resolved: {task_result.resolved} | "
            f"Test exit: {task_result.test_exit_code} | "
            f"Tool calls: {getattr(task_result, 'tool_calls', getattr(task_result, 'tool_calls_used', 0))} | "
            f"Duration: {task_result.duration_seconds:.1f}s"
        )
        if task_result.error:
            print(f"Error: {task_result.error}")
else:
    print("[EVALUATOR] No aggregate result object was returned; the next cells will export any partial files.")
""")

    set_cell(9, r"""# 8. Read available evaluator artifacts without discarding partial runs.
summary_file = RESULTS_DIR / "summary.json"
task_results_file = RESULTS_DIR / "task_results.jsonl"
summary_data = {}
if summary_file.is_file():
    try:
        summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
        if not isinstance(summary_data, dict):
            summary_data = {"raw_summary": str(summary_data), "parse_warning": "summary was not a JSON object"}
    except Exception as exc:
        summary_data = {"parse_error": f"{type(exc).__name__}: {exc}"}
else:
    print("[PARTIAL] summary.json was not produced.")

task_records = []
record_parse_errors = []
if task_results_file.is_file():
    for line_number, line in enumerate(task_results_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if isinstance(record, dict):
                task_records.append(record)
            else:
                record_parse_errors.append(f"line {line_number}: record is not a JSON object")
        except Exception as exc:
            record_parse_errors.append(f"line {line_number}: {type(exc).__name__}: {exc}")
else:
    print("[PARTIAL] task_results.jsonl was not produced.")

records_by_id = {r.get("instance_id"): r for r in task_records if r.get("instance_id")}
missing_task_ids = [tid for tid in TARGET_TASK_IDS if tid not in records_by_id]
for task_id in TARGET_TASK_IDS:
    record = records_by_id.get(task_id)
    patch_file = RESULTS_DIR / "patches" / f"{task_id}.patch"
    test_log_file = RESULTS_DIR / "test_outputs" / f"{task_id}.log"
    print(
        f"{task_id}: record_present={record is not None} "
        f"resolved={record.get('resolved') if record else None} "
        f"test_exit_code={record.get('test_exit_code') if record else None} "
        f"patch={patch_file.is_file()} test_log={test_log_file.is_file()}"
    )
print(f"[COVERAGE] {len(records_by_id)}/{len(TARGET_TASK_IDS)} task records; missing={missing_task_ids}")
if record_parse_errors:
    print("[PARSE WARNINGS]", record_parse_errors)
print(json.dumps(summary_data, indent=2))
""")

    set_cell(10, r"""# 9. Export all available diagnostic artifacts only (never a leaderboard submission).
records = records_by_id
attempted_count = len(records)
resolved_count = sum(1 for r in records.values() if r.get("resolved") is True)
missing_task_ids = [tid for tid in TARGET_TASK_IDS if tid not in records]
diagnostic_summary = {
    "diagnostic_type": "V35_FOUR_REPOSITORY_RETRIEVAL_AND_GENERALIZATION",
    "is_leaderboard_submission": False,
    "candidate_zip_sha256": EXPECTED_ZIP_SHA256,
    "model": MODEL_NAME,
    "task_ids": TARGET_TASK_IDS,
    "total_tasks": len(TARGET_TASK_IDS),
    "attempted_tasks": attempted_count,
    "missing_task_ids": missing_task_ids,
    "resolved_tasks": resolved_count,
    "observed_resolution_rate_over_requested": resolved_count / len(TARGET_TASK_IDS),
    "resolution_rate_among_recorded": resolved_count / attempted_count if attempted_count else None,
    "evaluation_error": EVALUATION_ERROR,
    "summary_data": summary_data,
    "record_parse_errors": record_parse_errors,
    "eval_config": {
        "timeout_seconds": 300,
        "max_time_minutes": 5,
        "max_tool_calls": 40,
        "max_turns": 500,
    },
    "sampling": {
        "max_output_tokens": 4096,
        "thinking_budget": 1024,
        "include_thoughts": False,
    },
    "context_compaction": {
        "token_threshold": 14336,
        "compaction_interval": 15,
        "overlap_size": 2,
        "event_retention_size": 5,
    },
    "context_compaction_events": COMPACTION_COUNT,
    "results": [
        {
            "task_id": tid,
            "repo": EXPECTED_REPOS[tid],
            "record_present": tid in records,
            "resolved": records.get(tid, {}).get("resolved"),
            "test_exit_code": records.get(tid, {}).get("test_exit_code"),
            "error": records.get(tid, {}).get("error") if tid in records else "missing_result_record",
        }
        for tid in TARGET_TASK_IDS
    ],
    "note": "Private diagnostic only. Partial results are retained. No Kaggle competition submission is generated or uploaded.",
}
diagnostic_path = Path("/kaggle/working/v35_heldout_diagnostic.json")
diagnostic_path.write_text(json.dumps(diagnostic_summary, indent=2), encoding="utf-8")

artifacts_zip = Path("/kaggle/working/v35_heldout_diagnostic_artifacts.zip")
with zipfile.ZipFile(artifacts_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    if RESULTS_DIR.exists():
        for path in sorted(RESULTS_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, f"results/v35_heldout/{path.relative_to(RESULTS_DIR).as_posix()}")
    if (Path("/kaggle/working") / "v35_evaluation_exception.txt").is_file():
        archive.write(Path("/kaggle/working") / "v35_evaluation_exception.txt", "v35_evaluation_exception.txt")
    archive.write(diagnostic_path, "v35_heldout_diagnostic.json")

print(json.dumps(diagnostic_summary, indent=2))
print(f"Saved partial/full diagnostic traces, patches, and test logs: {artifacts_zip}")
parquet_artifacts = list(Path("/kaggle/working").rglob("*.parquet"))
assert not parquet_artifacts, f"Unexpected parquet artifact(s) found: {parquet_artifacts}"
print("[CONFIRMED] No leaderboard submission parquet file generated.")
""")

    for i, cell in enumerate(cells):
        cell["id"] = f"v35-cell-{i}"

    joined = "\n".join(get(i) for i in range(len(cells)))
    runtime_cell = get(8)
    summary_cell = get(10)
    for required in ("timeout_seconds=300", "max_time_minutes=5", "max_tool_calls=40", "max_turns=500"):
        if required not in runtime_cell:
            raise SystemExit(f"Diagnostic runtime budget mismatch: missing {required}")
    for required in ('"timeout_seconds": 300', '"max_time_minutes": 5', '"max_tool_calls": 40', '"max_turns": 500'):
        if required not in summary_cell:
            raise SystemExit(f"Diagnostic summary budget mismatch: missing {required}")
    if "15 minutes per task" in joined:
        raise SystemExit("Stale fifteen-minute diagnostic description remains.")
    if "5 minutes per task" not in joined:
        raise SystemExit("Five-minute diagnostic budget is not documented.")
    if "AUTHORIZE_GPU_SMOKE_TEST = False" not in joined:
        raise SystemExit("GPU execution gate is not closed.")
    if "MODEL_NAME = \"gemma-4-31b-it-qat-w4a16-ct\"" not in joined:
        raise SystemExit("Wrong model in diagnostic notebook.")
    if "gemma4-v35-candidate" not in joined or "EXPECTED_FILE_HASHES" not in joined:
        raise SystemExit("Diagnostic notebook does not pin the v35 candidate dataset.")
    if "submit_prediction" in joined.lower():
        raise SystemExit("Leaderboard submission code found in diagnostic notebook.")
    if "EVALUATION_ERROR" not in runtime_cell or "missing_task_ids" not in get(9) or "attempted_tasks" not in summary_cell:
        raise SystemExit("Diagnostic notebook must preserve partial evaluator failures and missing task records.")
    if "Partial results are retained" not in summary_cell:
        raise SystemExit("Diagnostic partial-result retention note is missing.")
    if "v31" in joined:
        raise SystemExit("Stale v31 reference remains in notebook source.")

    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]), filename=f"cell-{i}")
        if cell.get("outputs", []) != []:
            raise SystemExit(f"Cell {i} still has execution outputs.")
        if cell["cell_type"] == "code" and cell.get("execution_count") is not None:
            raise SystemExit(f"Cell {i} has a non-null execution count.")

    metadata = json.loads(SOURCE_META.read_text(encoding="utf-8"))
    metadata.update({
        "id": "ronak1167/gemma-4-swe-agent-v35-retrieval-diagnostic",
        "title": "Gemma 4 SWE Agent v35 Retrieval and Generalization Diagnostic",
        "code_file": "kaggle_mini_benchmark.ipynb",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": False,
        "dataset_sources": ["ronak1167/gemma4-v35-candidate", "metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": ["google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2"],
    })

    OUT.mkdir(parents=True, exist_ok=True)
    notebook_path = OUT / "kaggle_mini_benchmark.ipynb"
    metadata_path = OUT / "kernel-metadata.json"
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "notebook": str(notebook_path),
        "metadata": str(metadata_path),
        "candidate_sha256": sha(ARCHIVE),
        "candidate_files": len(FILES),
        "task_ids": ["fastapi_14458", "rich_4075", "requests_7309", "httpx_3672"],
        "context_compaction": {"token_threshold": 14336, "compaction_interval": 15, "overlap_size": 2, "event_retention_size": 5},
        "gpu_gate": "CLOSED",
        "leaderboard_submission": False,
        "static_validation": "PASS",
    }, indent=2))


if __name__ == "__main__":
    main()
