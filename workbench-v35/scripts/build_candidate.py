from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "workbench-v35" / "agent"
ARCHIVE = ROOT / "dist" / "submission-v35.zip"
DATASET = ROOT / "dist" / "kaggle_v35_candidate_dataset"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
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


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_yaml(path: Path):
    class Loader(yaml.SafeLoader):
        pass
    Loader.add_constructor("!include", lambda loader, node: loader.construct_scalar(node))
    return yaml.load(path.read_text(encoding="utf-8"), Loader=Loader)


def validate_sources() -> dict[str, str]:
    sys.dont_write_bytecode = True
    for cache in AGENT.rglob("__pycache__"):
        shutil.rmtree(cache)
    missing = [name for name in FILES if not (AGENT / name).is_file()]
    if missing:
        raise SystemExit(f"Missing v35 files: {missing}")
    expected_paths = {(AGENT / name).resolve() for name in FILES}
    unexpected = [p for p in AGENT.rglob("*") if p.is_file() and p.resolve() not in expected_paths]
    if unexpected:
        raise SystemExit(f"Unexpected files in candidate source tree: {unexpected}")

    hashes = {name: digest((AGENT / name).read_bytes()) for name in FILES}
    root = read_yaml(AGENT / "agent.yaml")
    sub = read_yaml(AGENT / "sub_agents" / "code_analyzer.yaml")
    evaluation = yaml.safe_load((AGENT / "eval_config.yaml").read_text(encoding="utf-8"))
    sampling = yaml.safe_load((AGENT / "configs" / "sampling.yaml").read_text(encoding="utf-8"))

    if root.get("model") != MODEL or sub.get("model") != MODEL:
        raise SystemExit("Root and analyzer must use the same permitted 31B model.")
    if root.get("instruction") != "prompts/system.md":
        raise SystemExit("Root instruction include path mismatch.")
    if root.get("skills") != ["skills/public_issue_memory"]:
        raise SystemExit("Public issue memory skill is not declared correctly.")

    names = {item for item in root.get("tools", []) if isinstance(item, str)}
    required = {
        "run_command", "submit_patch", "get_status", "read_file",
        "edit_file", "write_file", "get_code_neighbors",
        "search_similar_code", "get_code_subgraph", "load_skill",
        "run_skill_script",
    }
    if not required.issubset(names):
        raise SystemExit(f"Missing root tools: {sorted(required - names)}")
    agent_tools = [item["agent_tool"] for item in root["tools"] if isinstance(item, dict) and "agent_tool" in item]
    if len(agent_tools) != 1 or agent_tools[0].get("config_path") != "sub_agents/code_analyzer.yaml" or agent_tools[0].get("skip_summarization") is not True:
        raise SystemExit("Read-only analyzer AgentTool declaration is invalid.")
    if set(sub.get("tools", [])) != {"read_file", "search_similar_code", "get_code_neighbors", "get_code_subgraph"}:
        raise SystemExit("Analyzer must remain read-only and use only code-intelligence tools.")

    if evaluation.get("evaluation") != {
        "timeout_seconds": 300,
        "max_tool_calls": 40,
        "max_time_minutes": 5,
        "max_turns": 500,
    }:
        raise SystemExit("Evaluation budget differs from the validated v35 envelope.")
    thinking = sampling.get("thinking_config", {})
    if sampling.get("max_output_tokens") != 4096 or thinking.get("thinking_budget") != 1024 or thinking.get("include_thoughts") is not False:
        raise SystemExit("Sampling configuration differs from the validated 4096/1024 envelope.")

    include_checks = [
        (AGENT / "agent.yaml", "prompts/system.md"),
        (AGENT / "agent.yaml", "configs/sampling.yaml"),
        (AGENT / "sub_agents" / "code_analyzer.yaml", "analyzer.md"),
    ]
    for config_path, rel in include_checks:
        resolved = (config_path.parent / rel).resolve()
        if AGENT.resolve() not in resolved.parents or not resolved.is_file():
            raise SystemExit(f"Unsafe or missing include: {config_path.name} -> {rel}")

    prompt = (AGENT / "prompts" / "system.md").read_text(encoding="utf-8")
    if "{problem_description}" not in prompt:
        raise SystemExit("Persistent active-issue anchor is missing.")
    if "hidden test_patch is NOT present in Container A" not in prompt:
        raise SystemExit("Critical hidden-test visibility correction is missing.")
    if "No hardcoded issue-to-patch registry" not in prompt:
        raise SystemExit("Anti-registry safeguard is missing.")
    if "submit_patch() as the final tool action" not in prompt:
        raise SystemExit("Safe final submission protocol is missing.")
    if "Hard task budget is five minutes (300 seconds)" not in prompt:
        raise SystemExit("Prompt hard budget must match the five-minute evaluator cap.")
    if "fifteen minutes" in prompt or "90?180" in prompt:
        raise SystemExit("Prompt contains stale or corrupted timing guidance.")
    if "60 to 120 seconds" not in prompt:
        raise SystemExit("Prompt lacks a realistic focused-test time target.")
    if "git diff -- tests/" in prompt:
        raise SystemExit("Prompt still instructs inspection of the unavailable hidden test patch.")

    index_path = AGENT / "skills" / "public_issue_memory" / "assets" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if len(index) != 129 or len({x["instance_id"] for x in index}) != 129:
        raise SystemExit("Public issue-memory corpus must contain 129 unique task records.")
    if any("patch" in x or "test_patch" in x for x in index):
        raise SystemExit("Gold patch bodies must not be packaged in the retrieval corpus.")
    search_source = (AGENT / "skills" / "public_issue_memory" / "scripts" / "search.py").read_text(encoding="utf-8")
    ast.parse(search_source)
    forbidden_secrets = re.compile(r"(?:hf_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9]{24,}|KAGGLE_KEY\s*[:=])", re.I)
    for name in FILES:
        raw = (AGENT / name).read_bytes()
        if forbidden_secrets.search(raw.decode("utf-8", "ignore")):
            raise SystemExit(f"Possible credential material found in {name}")
    return hashes


def write_archive(destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="v35-", suffix=".zip", dir=destination.parent, delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for name in FILES:
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                zf.writestr(info, (AGENT / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temp, "r") as zf:
            if zf.namelist() != list(FILES) or zf.testzip() is not None:
                raise SystemExit("ZIP member order, membership, or CRC validation failed.")
            for name in FILES:
                if zf.read(name) != (AGENT / name).read_bytes():
                    raise SystemExit(f"ZIP source mismatch: {name}")
        temp.replace(destination)
    finally:
        if temp.exists():
            temp.unlink()
    return digest(destination.read_bytes())


def retrieval_quality(index: list[dict]) -> dict:
    script = AGENT / "skills" / "public_issue_memory" / "scripts" / "search.py"
    spec = importlib.util.spec_from_file_location("v35_search", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    metrics = {
        "full_text": {"top1_same_repo": 0, "same_repo_rr": 0.0, "file_hits": 0, "file_overlap": 0, "file_total": 0},
        "short_query": {"top1_same_repo": 0, "same_repo_rr": 0.0, "file_hits": 0, "file_overlap": 0, "file_total": 0},
    }
    for target in index:
        target_files = set(target.get("changed_files", []))
        queries = {
            "full_text": target.get("problem_statement", ""),
            "short_query": " ".join(module.tokenize(target.get("problem_statement", ""))[:12]),
        }
        for label, query in queries.items():
            exclude_id = target["instance_id"] if label == "short_query" else None
            if label == "full_text":
                assert module.exact_self_match(index, query) == target["instance_id"], f"Auto self-match failed for {target['instance_id']}"
            results = module.search(index, query, target.get("repo"), exclude_id, 3)
            assert all(result["instance_id"] != target["instance_id"] for result in results), f"Self-retrieval leak for {target['instance_id']}"
            if not results:
                continue
            m = metrics[label]
            if results[0]["repo"] == target["repo"]:
                m["top1_same_repo"] += 1
            retrieved_files = set()
            rank = None
            for rank_index, result in enumerate(results, start=1):
                retrieved_files.update(result.get("changed_files", []))
                if rank is None and result["repo"] == target["repo"]:
                    rank = rank_index
            if rank is not None:
                m["same_repo_rr"] += 1.0 / rank
            if target_files:
                overlap = target_files & retrieved_files
                m["file_overlap"] += len(overlap)
                m["file_total"] += len(target_files)
                if overlap:
                    m["file_hits"] += 1

    count = len(index)
    output = {}
    for label, m in metrics.items():
        output[label] = {
            "top1_same_repo_rate": round(m["top1_same_repo"] / count, 4),
            "same_repo_mrr_at_3": round(m["same_repo_rr"] / count, 4),
            "changed_file_recall_at_3": round(m["file_overlap"] / m["file_total"], 4) if m["file_total"] else 0,
            "tasks_with_any_changed_file_hit_at_3": round(m["file_hits"] / count, 4),
        }
    output["leave_one_out_queries"] = count
    output["interpretation"] = "Retrieval-localization diagnostic only; not an agent-resolution or leaderboard score."
    return output


def run_self_tests() -> dict:
    index = json.loads((AGENT / "skills" / "public_issue_memory" / "assets" / "index.json").read_text(encoding="utf-8"))
    search_script = AGENT / "skills" / "public_issue_memory" / "scripts" / "search.py"
    spec = importlib.util.spec_from_file_location("v35_search_test", search_script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    sample = index[0]
    assert module.exact_self_match(index, sample["problem_statement"]) == sample["instance_id"]
    results = module.search(index, sample["problem_statement"], sample["repo"], None, 3)
    assert len(results) <= 3
    assert all(x["instance_id"] != sample["instance_id"] for x in results)
    assert all("patch" not in x and "test_patch" not in x for x in results)
    assert len({x["instance_id"] for x in results}) == len(results)

    # Reproduce the ADK skill runner materialization layout: scripts/ and assets/ are copied into one temp root.
    with tempfile.TemporaryDirectory(prefix="v35-skill-materialization-") as td:
        skill_root = Path(td)
        (skill_root / "scripts").mkdir()
        (skill_root / "assets").mkdir()
        shutil.copy2(search_script, skill_root / "scripts" / "search.py")
        shutil.copy2(AGENT / "skills" / "public_issue_memory" / "assets" / "index.json", skill_root / "assets" / "index.json")
        run = subprocess.run(
            [sys.executable, str(skill_root / "scripts" / "search.py"), "--query", sample["problem_statement"], "--repo", sample["repo"], "--top_k", "3"],
            cwd=skill_root, capture_output=True, text=True, timeout=20,
        )
        assert run.returncode == 0, f"Materialized skill script failed: {run.stderr}"
        payload = json.loads(run.stdout)
        assert payload["results"], "Materialized skill script returned no results."
        assert payload["auto_excluded_instance_id"] == sample["instance_id"], "Materialized skill failed exact self-exclusion."
        assert len(run.stdout) <= 3800, "Skill output exceeded its strict response budget."

    with tempfile.TemporaryDirectory(prefix="v35-determinism-") as td:
        one = Path(td) / "one.zip"
        two = Path(td) / "two.zip"
        h1 = write_archive(one)
        h2 = write_archive(two)
        assert h1 == h2, "Archive build is not deterministic."

    return {
        "retrieval_unit_checks": "PASS",
        "leave_one_out_retrieval": retrieval_quality(index),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if ARCHIVE.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite versioned archive: {ARCHIVE}")
    if DATASET.exists() and any(DATASET.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to overwrite existing candidate staging: {DATASET}")

    hashes = validate_sources()
    tests = run_self_tests()
    archive_hash = write_archive(ARCHIVE)

    if DATASET.exists():
        shutil.rmtree(DATASET)
    DATASET.mkdir(parents=True)
    for name in FILES:
        target = DATASET / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AGENT / name, target)
    shutil.copy2(ARCHIVE, DATASET / "submission-v35.zip")

    metadata = {
        "title": "Gemma 4 SWE Agent v35 Candidate",
        "id": "ronak1167/gemma4-v35-candidate",
        "licenses": [{"name": "CC0-1.0"}],
    }
    (DATASET / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "candidate": "v35",
        "model": MODEL,
        "archive": str(ARCHIVE),
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": archive_hash,
        "archive_members": list(FILES),
        "source_sha256": hashes,
        "eval_config": {"timeout_seconds": 300, "max_tool_calls": 40, "max_time_minutes": 5, "max_turns": 500},
        "sampling": {"max_output_tokens": 4096, "thinking_budget": 1024, "include_thoughts": False},
        "public_issue_memory": {"tasks": 129, "gold_patch_bodies_included": False},
        "self_tests": tests,
        "leaderboard_submitted": False,
        "gpu_evaluation_run": False,
    }
    (DATASET / "candidate-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report_path = ROOT / "workbench-v35" / "reports" / "build-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
