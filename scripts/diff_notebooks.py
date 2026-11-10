import json
import difflib
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    p_dist = root / "dist/kaggle_kernel/kaggle_smoke_test.ipynb"
    p_cloud = root / "reports/version-19-final-cloud-readback/gemma-4-swe-agent-smoke-test.ipynb"

    nb_dist = json.loads(p_dist.read_text(encoding="utf-8"))
    nb_cloud = json.loads(p_cloud.read_text(encoding="utf-8"))

    print(f"dist cells count: {len(nb_dist.get('cells', []))}")
    print(f"cloud cells count: {len(nb_cloud.get('cells', []))}")

    # Compare cell sources
    cells_dist = nb_dist.get("cells", [])
    cells_cloud = nb_cloud.get("cells", [])

    diff_found = False
    for idx, (c_d, c_c) in enumerate(zip(cells_dist, cells_cloud)):
        src_d = "".join(c_d.get("source", []))
        src_c = "".join(c_c.get("source", []))
        if src_d != src_c:
            diff_found = True
            print(f"\n--- Diff in cell {idx} ({c_d.get('cell_type')}) ---")
            diff = list(difflib.unified_diff(
                src_d.splitlines(),
                src_c.splitlines(),
                fromfile=f"dist cell {idx}",
                tofile=f"cloud cell {idx}",
                lineterm=""
            ))
            for line in diff:
                print(f"  {line}")

    if not diff_found:
        print("\nAll cell sources are IDENTICAL!")
        # check metadata or execution count differences
        print("Checking notebook metadata / execution_count...")
        for idx, (c_d, c_c) in enumerate(zip(cells_dist, cells_cloud)):
            if c_d.get("execution_count") != c_c.get("execution_count"):
                print(f"  Cell {idx} execution_count: dist={c_d.get('execution_count')}, cloud={c_c.get('execution_count')}")
            if c_d.get("outputs") != c_c.get("outputs"):
                print(f"  Cell {idx} outputs differ!")
            if c_d.get("metadata") != c_c.get("metadata"):
                print(f"  Cell {idx} metadata differs: dist={c_d.get('metadata')}, cloud={c_c.get('metadata')}")

        meta_diff = list(difflib.unified_diff(
            json.dumps(nb_dist.get("metadata", {}), indent=2).splitlines(),
            json.dumps(nb_cloud.get("metadata", {}), indent=2).splitlines(),
            fromfile="dist metadata",
            tofile="cloud metadata",
            lineterm=""
        ))
        if meta_diff:
            print("\nTop-level notebook metadata diff:")
            for line in meta_diff:
                print(f"  {line}")

if __name__ == "__main__":
    main()

