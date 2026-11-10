import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    tasks_file = root / "starter/official/tasks.jsonl"
    for line in tasks_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        if task.get("instance_id") == "rich_4077":
            print("Task: rich_4077")
            print("repo:", task.get("repo"))
            print("base_commit:", task.get("base_commit"))
            print("problem_statement:\n", task.get("problem_statement"))
            print("test_patch:\n", task.get("test_patch"))
            break

if __name__ == "__main__":
    main()

