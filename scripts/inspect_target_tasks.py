import json

tasks = [json.loads(line) for line in open('starter/official/tasks.jsonl', encoding='utf-8') if line.strip()]
by_id = {t['instance_id']: t for t in tasks}
for tid in ['fastapi_15589', 'rich_4077', 'rich_3944']:
    t = by_id[tid]
    print(f"\n==========================================")
    print(f"=== {tid} ({t.get('repo')}) ===")
    print(f"==========================================")
    print("PROBLEM STATEMENT:")
    print(t.get('problem_statement')[:400])
    print("\nGOLD PATCH:")
    print(t.get('patch'))
    print("\nTEST PATCH:")
    print(t.get('test_patch'))

