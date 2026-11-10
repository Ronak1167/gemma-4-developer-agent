import json

tasks_path = "starter/official/tasks.jsonl"
with open(tasks_path, "r", encoding="utf-8") as f:
    for line in f:
        t = json.loads(line)
        if t["instance_id"] == "rich_4077":
            print("=== TARGET TASK: rich_4077 ===")
            print("Repo:", t.get("repo"))
            print("Base commit:", t.get("base_commit"))
            print("\nProblem statement:")
            print(t.get("problem_statement"))
            print("\nTest patch:")
            print(t.get("test_patch"))
            print("\nGold patch:")
            print(t.get("patch"))
            break

