import json
from pathlib import Path

trace = json.loads(Path('reports/gpu-diagnostic-v22-output/results/mini_benchmark/traces/trace_rich_3944.json').read_text(encoding='utf-8'))
steps = trace['steps']

print(f"Total steps in rich_3944: {len(steps)}")
for i in [5, 6, 7, 14, 15, 16, 17, 18]:
    s = steps[i]
    m = s.get('metrics') or s.get('extra', {}).get('usage') or {}
    print(f"--- Step {i} ---")
    print("source:", s.get('source'))
    print("metrics:", m)
    msg = s.get('message')
    if isinstance(msg, dict):
        print("role:", msg.get('role'))
        print("content:", str(msg.get('content'))[:100])
        print("thought:", str(msg.get('thought') or msg.get('reasoning_content'))[:100])
    else:
        print("msg string:", str(msg)[:150])
    obs = s.get('observation')
    if obs:
        print("obs:", str(obs)[:150])

