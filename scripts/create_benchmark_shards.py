import json
from collections import Counter, defaultdict
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    manifest = root / "starter/official/tasks.jsonl"
    tasks = [json.loads(x) for x in manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(tasks) == 129
    shards = [[] for _ in range(4)]
    per_repo = [Counter() for _ in range(4)]
    for task in tasks:
        repo = task["repo"]
        target = min(range(4), key=lambda i: (per_repo[i][repo], len(shards[i]), i))
        shards[target].append(task)
        per_repo[target][repo] += 1
    ids = [[t["instance_id"] for t in shard] for shard in shards]
    flat = [x for shard in ids for x in shard]
    assert len(flat) == len(set(flat)) == 129
    assert set(flat) == {t["instance_id"] for t in tasks}
    payload = {
        "source_manifest": "starter/official/tasks.jsonl",
        "task_count": len(tasks),
        "shard_count": 4,
        "strategy": "deterministic greedy stratification by repository, then current shard size",
        "shards": [
            {
                "shard": i,
                "task_count": len(shard),
                "repo_counts": dict(Counter(t["repo"] for t in shard)),
                "task_ids": [t["instance_id"] for t in shard],
                "estimated_active_hours_at_450s_per_task": round(len(shard) * 450 / 3600, 2),
                "estimated_active_hours_at_578s_per_task": round(len(shard) * 578 / 3600, 2),
            }
            for i, shard in enumerate(shards)
        ],
    }
    out = root / "reports/benchmark-shards.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Task counts:", [len(x) for x in shards])
    for item in payload["shards"]:
        print("Shard", item["shard"], "count", item["task_count"], "repos", item["repo_counts"])
        print("  estimated active hours:", item["estimated_active_hours_at_450s_per_task"], "to", item["estimated_active_hours_at_578s_per_task"])
    print("[PASS] Every official task appears exactly once across four shards.")


if __name__ == "__main__":
    main()
