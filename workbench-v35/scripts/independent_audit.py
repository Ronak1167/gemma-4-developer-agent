from __future__ import annotations
import ast, hashlib, json, re, subprocess, sys, zipfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "workbench-v35" / "agent"
ZIP = ROOT / "dist" / "submission-v35.zip"
NOTEBOOK = ROOT / "dist" / "kaggle_v35_diagnostic" / "kaggle_mini_benchmark.ipynb"
META = ROOT / "dist" / "kaggle_v35_diagnostic" / "kernel-metadata.json"
TASKS = ROOT / "starter" / "official" / "tasks.jsonl"
EXPECTED = (
    "agent.yaml", "eval_config.yaml", "configs/sampling.yaml",
    "prompts/system.md", "sub_agents/code_analyzer.yaml",
    "sub_agents/analyzer.md", "skills/public_issue_memory/SKILL.md",
    "skills/public_issue_memory/scripts/search.py",
    "skills/public_issue_memory/assets/index.json",
)
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok: bool, message: str) -> None:
    if not ok: raise AssertionError(message)
def main() -> None:
    check(ZIP.is_file() and NOTEBOOK.is_file() and META.is_file(), "v35 artifacts missing")
    class IncludeLoader(yaml.SafeLoader): pass
    IncludeLoader.add_constructor("!include", lambda loader, node: loader.construct_scalar(node))
    root = yaml.load((AGENT/"agent.yaml").read_text(encoding="utf-8"), Loader=IncludeLoader)
    sub = yaml.load((AGENT/"sub_agents/code_analyzer.yaml").read_text(encoding="utf-8"), Loader=IncludeLoader)
    ev = yaml.safe_load((AGENT/"eval_config.yaml").read_text(encoding="utf-8"))["evaluation"]
    sampling = yaml.safe_load((AGENT/"configs/sampling.yaml").read_text(encoding="utf-8"))
    check(root["model"] == sub["model"] == "gemma-4-31b-it-qat-w4a16-ct", "model mismatch")
    check(ev == {"timeout_seconds":300,"max_tool_calls":40,"max_time_minutes":5,"max_turns":500}, "eval config drift")
    prompt = (AGENT/"prompts/system.md").read_text(encoding="utf-8")
    check("Hard task budget is five minutes (300 seconds)" in prompt, "prompt/eval budget mismatch")
    check("fifteen minutes" not in prompt and "90?180" not in prompt, "stale/corrupt timing guidance")
    check("60 to 120 seconds" in prompt, "focused-test budget missing")
    check("{problem_description}" in prompt and "submit_patch() as the final tool action" in prompt, "core prompt contract missing")
    check("hidden test_patch is NOT present in Container A" in prompt, "hidden test boundary missing")
    check("No hardcoded issue-to-patch registry" in prompt, "anti-registry safeguard missing")
    check(set(sub["tools"]) == {"read_file","search_similar_code","get_code_neighbors","get_code_subgraph"}, "analyzer is not read-only")
    check(root["instruction"] == "prompts/system.md", "root include mismatch")
    # Parse includes and enforce exact archive membership and byte identity.
    with zipfile.ZipFile(ZIP) as z:
        check(z.namelist() == list(EXPECTED), "unexpected archive membership/order")
        check(z.testzip() is None, "archive CRC failure")
        for name in EXPECTED:
            check(z.read(name) == (AGENT/name).read_bytes(), f"archive/source mismatch: {name}")
    # Notebook: AST, clean outputs, closed gate, private/offline, exact budgets and hash pins.
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    joined = "\n".join("".join(c.get("source",[])) for c in cells)
    for i,c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell-{i}")
            check(c.get("outputs",[]) == [] and c.get("execution_count") is None, f"notebook cell {i} has stale outputs")
    check("AUTHORIZE_GPU_SMOKE_TEST = False" in joined, "GPU gate is not closed")
    check("gemma-4-31b-it-qat-w4a16-ct" in joined, "notebook model mismatch")
    for s in ("timeout_seconds=300","max_time_minutes=5","max_tool_calls=40","max_turns=500",
              '"timeout_seconds": 300','"max_time_minutes": 5','"max_tool_calls": 40','"max_turns": 500'):
        check(s in joined, f"notebook budget mismatch: {s}")
    check("submit_prediction" not in joined.lower() and "is_leaderboard_submission" in joined, "submission code/guard check failed")
    check("EVALUATION_ERROR" in joined and "missing_task_ids" in joined and "attempted_tasks" in joined, "partial diagnostic recovery missing")
    check("Partial results are retained" in joined, "partial-result export note missing")
    check(sha(ZIP) in joined, "notebook does not pin archive SHA")
    meta = json.loads(META.read_text(encoding="utf-8"))
    check(meta["is_private"] is True and meta["enable_gpu"] is True and meta["enable_internet"] is False, "Kaggle privacy/GPU/network metadata invalid")
    check(any(x.endswith("/gemma4-v35-candidate") for x in meta["dataset_sources"]), "wrong candidate dataset")
    # Official task manifest: all four are unique, real, repo-matched, test-patched tasks.
    tasks = [json.loads(x) for x in TASKS.read_text(encoding="utf-8").splitlines() if x.strip()]
    byid = {x["instance_id"]:x for x in tasks}
    check(len(tasks)==129 and len(byid)==129, "official manifest count/uniqueness mismatch")
    targets={"fastapi_14458":"fastapi/fastapi","rich_4075":"Textualize/rich","requests_7309":"psf/requests","httpx_3672":"encode/httpx"}
    for tid,repo in targets.items():
        check(tid in byid and byid[tid]["repo"]==repo and bool(byid[tid].get("test_patch")), f"invalid diagnostic task: {tid}")
    # Retrieval: exhaustive exact-self-exclusion and response-size smoke tests.
    index=json.loads((AGENT/"skills/public_issue_memory/assets/index.json").read_text(encoding="utf-8"))
    check(len(index)==129 and len({x["instance_id"] for x in index})==129, "retrieval corpus invalid")
    check(not any("patch" in x or "test_patch" in x for x in index), "gold patch material in corpus")
    import importlib.util
    spec=importlib.util.spec_from_file_location("v35_search_audit", AGENT/"skills/public_issue_memory/scripts/search.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for x in index:
        q=x["problem_statement"]
        results=module.search(index,q,x["repo"],x["instance_id"],3)
        check(all(y["instance_id"] != x["instance_id"] for y in results), f"self leak: {x['instance_id']}")
        payload={"source":"official public development-task metadata; retrieval hints only","query":q[:240],"repo_filter":x["repo"],"auto_excluded_instance_id":module.exact_self_match(index,q),"results":results,"warning":"Analogies are not proof."}
        check(len(json.dumps(payload,separators=(",",":"))) <= 3800, f"retrieval output too large: {x['instance_id']}")
    # Ensure all candidate files are represented exactly once and no accidental secrets are packaged.
    for name in EXPECTED:
        raw=(AGENT/name).read_text(encoding="utf-8")
        check(not re.search(r"(?:hf_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9]{24,}|KAGGLE_KEY\s*[:=])",raw,re.I), f"possible secret in {name}")
    report=json.loads((ROOT/"workbench-v35/reports/build-report.json").read_text(encoding="utf-8"))
    check(report["archive_sha256"]==sha(ZIP) and report["archive_bytes"]==ZIP.stat().st_size, "build report hash/size mismatch")
    print(json.dumps({
      "result":"PASS","archive_sha256":sha(ZIP),"archive_bytes":ZIP.stat().st_size,
      "archive_files":len(EXPECTED),"notebook_cells":len(cells),
      "official_tasks":len(tasks),"retrieval_self_exclusion":"129/129",
      "diagnostic_tasks":list(targets),"gpu_gate":"CLOSED",
      "leaderboard_submission":False
    },indent=2))
if __name__=="__main__": main()
