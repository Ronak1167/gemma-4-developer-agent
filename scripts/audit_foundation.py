import hashlib
import json
import difflib
from pathlib import Path

def get_hash(path: Path) -> str:
    if not path.exists():
        return "FILE_NOT_FOUND"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    root = Path(__file__).resolve().parent.parent
    print(f"=== PHASE 1: FOUNDATION AND SMOKE TEST AUDIT ===")
    print(f"Workspace: {root}\n")

    # 1. Hashes of Core Agent & Notebook Files
    files_to_hash = [
        "agent/agent.yaml",
        "agent/configs/sampling.yaml",
        "agent/prompts/system.md",
        "experiments/kaggle_smoke_test.ipynb",
        "dist/kaggle_kernel/kaggle_smoke_test.ipynb",
        "reports/version-19-final-cloud-readback/gemma-4-swe-agent-smoke-test.ipynb",
        "reports/version-19-final-cloud-readback/kernel-metadata.json",
        "dist/submission-baseline.zip",
        "reports/version-18-smoke-test-output/results/smoke_test/patches/rich_4077.patch",
        "reports/version-18-smoke-test-output/results/smoke_test/test_outputs/rich_4077.log",
        "reports/version-18-smoke-test-output/results/smoke_test/task_results.jsonl",
        "reports/version-18-smoke-test-output/results/smoke_test/summary.json",
        "reports/version-18-smoke-test-output/smoke_test_diagnostic.json",
    ]

    hashes = {}
    print("--- File Hashes ---")
    for rel_path in files_to_hash:
        p = root / rel_path
        h = get_hash(p)
        hashes[rel_path] = h
        size = p.stat().st_size if p.exists() else 0
        print(f"  {rel_path}: {h} ({size} bytes)")

    # 2. Check notebook consistency between dist, experiments, and cloud readback
    p_dist = root / "dist/kaggle_kernel/kaggle_smoke_test.ipynb"
    p_exp = root / "experiments/kaggle_smoke_test.ipynb"
    p_cloud = root / "reports/version-19-final-cloud-readback/gemma-4-swe-agent-smoke-test.ipynb"

    print("\n--- Notebook Consistency Check ---")
    dist_cloud_match = (hashes.get("dist/kaggle_kernel/kaggle_smoke_test.ipynb") == 
                        hashes.get("reports/version-19-final-cloud-readback/gemma-4-swe-agent-smoke-test.ipynb"))
    exp_dist_match = (hashes.get("experiments/kaggle_smoke_test.ipynb") == 
                      hashes.get("dist/kaggle_kernel/kaggle_smoke_test.ipynb"))
    print(f"  dist/kaggle_kernel == version-19 cloud readback: {dist_cloud_match}")
    print(f"  experiments == dist/kaggle_kernel: {exp_dist_match}")

    if not exp_dist_match and p_exp.exists() and p_dist.exists():
        diff = list(difflib.unified_diff(
            p_dist.read_text(encoding="utf-8").splitlines(),
            p_exp.read_text(encoding="utf-8").splitlines(),
            fromfile="dist/kaggle_kernel",
            tofile="experiments",
            lineterm=""
        ))
        print(f"  Diff between dist and experiments ({len(diff)} lines):")
        for line in diff[:20]:
            print(f"    {line}")

    # 3. Check execution gate in all notebooks
    print("\n--- Execution Gate Check ---")
    for name, p in [("dist", p_dist), ("experiments", p_exp), ("cloud", p_cloud)]:
        if p.exists():
            nb = json.loads(p.read_text(encoding="utf-8"))
            gate_found = False
            gate_value = None
            for cell in nb.get("cells", []):
                src = "".join(cell.get("source", []))
                for line in src.splitlines():
                    if "AUTHORIZE_GPU_SMOKE_TEST" in line and "=" in line:
                        gate_found = True
                        gate_value = line.strip()
            print(f"  {name}: gate found={gate_found}, value='{gate_value}'")

    # 4. Check Version 18 Patch against Official Task Reference
    print("\n--- Version 18 Patch vs Official Reference ---")
    tasks_file = root / "starter/official/tasks.jsonl"
    rich_task = None
    if tasks_file.exists():
        for line in tasks_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("instance_id") == "rich_4077":
                rich_task = rec
                break

    if rich_task:
        print(f"  Official task rich_4077 found:")
        print(f"    repo: {rich_task.get('repo')}")
        print(f"    base_commit: {rich_task.get('base_commit')}")
        print(f"    official patch:\n{rich_task.get('patch')}")
        print(f"    official test_patch:\n{rich_task.get('test_patch')}")
    else:
        print("  WARNING: rich_4077 not found in starter/official/tasks.jsonl")

    v18_patch_file = root / "reports/version-18-smoke-test-output/results/smoke_test/patches/rich_4077.patch"
    if v18_patch_file.exists() and rich_task:
        v18_patch_content = v18_patch_file.read_text(encoding="utf-8")
        print(f"\n  Version 18 generated patch:\n{v18_patch_content}")
        # Extract added lines from official vs v18
        official_added = [line for line in rich_task.get("patch", "").splitlines() if line.startswith("+") and not line.startswith("+++")]
        v18_added = [line for line in v18_patch_content.splitlines() if line.startswith("+") and not line.startswith("+++")]
        print(f"  Official added lines: {official_added}")
        print(f"  Version 18 added lines: {v18_added}")
        print(f"  Added source lines match exactly: {official_added == v18_added}")

    # 5. Check Version 18 Task Result and Test Output
    print("\n--- Version 18 Task Result & Test Output ---")
    tr_file = root / "reports/version-18-smoke-test-output/results/smoke_test/task_results.jsonl"
    if tr_file.exists():
        tr = json.loads(tr_file.read_text(encoding="utf-8").strip())
        print(f"  task_results.jsonl: resolved={tr.get('resolved')}, exit_code={tr.get('test_exit_code')}, tool_calls={tr.get('tool_calls')}, llm_calls={tr.get('total_llm_calls')}, duration={tr.get('duration_seconds')}s")

    test_out_file = root / "reports/version-18-smoke-test-output/results/smoke_test/test_outputs/rich_4077.log"
    if test_out_file.exists():
        print(f"  test_outputs/rich_4077.log content:\n{test_out_file.read_text(encoding='utf-8')}")

if __name__ == "__main__":
    main()

