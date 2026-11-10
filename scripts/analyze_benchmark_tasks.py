import json
from collections import Counter
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    tasks_file = root / "starter/official/tasks.jsonl"
    
    if not tasks_file.exists():
        print("ERROR: starter/official/tasks.jsonl not found!")
        return

    tasks = []
    repos = Counter()
    has_hints = 0
    has_test_patch = 0
    patch_sizes = []

    for line in tasks_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        tasks.append(task)
        repo = task.get("repo", "unknown")
        repos[repo] += 1
        if task.get("hints_text"):
            has_hints += 1
        if task.get("test_patch"):
            has_test_patch += 1
        if task.get("patch"):
            patch_sizes.append(len(task.get("patch").splitlines()))

    print(f"Total benchmark tasks: {len(tasks)}")
    print(f"Unique repositories: {len(repos)}")
    print("\nRepository distribution:")
    for repo, count in repos.most_common():
        print(f"  {repo}: {count} tasks ({count/len(tasks)*100:.1f}%)")

    print(f"\nMetadata stats:")
    print(f"  Tasks with hints: {has_hints}")
    print(f"  Tasks with test patch: {has_test_patch}")
    if patch_sizes:
        print(f"  Reference patch lines: min={min(patch_sizes)}, max={max(patch_sizes)}, avg={sum(patch_sizes)/len(patch_sizes):.1f}")

    # Inspect other official starter files
    starter_dir = root / "starter"
    print("\nStarter directory inspection:")
    for f in starter_dir.rglob("*"):
        if f.is_file():
            print(f"  {f.relative_to(starter_dir)} ({f.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

