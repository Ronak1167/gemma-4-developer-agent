import json
from pathlib import Path

traces_dir = Path("reports/gpu-diagnostic-v22-output/results/mini_benchmark/traces")
for p in traces_dir.glob("trace_*.json"):
    trace = json.loads(p.read_text(encoding='utf-8'))
    print(f"\n=== {p.name} (Steps: {len(trace['steps'])}) ===")
    for i, s in enumerate(trace['steps']):
        m = s.get('metrics') or s.get('extra', {}).get('usage') or {}
        tcs = [t.get('function_name') or t.get('name') for t in (s.get('tool_calls') or [])]
        msg = s.get('message', {})
        if isinstance(msg, dict):
            thought = msg.get('thought') or msg.get('reasoning_content')
            thought_len = len(str(thought)) if thought else 0
        else:
            thought_len = len(str(msg)) if '<|channel>thought' in str(msg) else 0
        print(f"Step {i:2d}: pt={m.get('prompt_tokens')} ct={m.get('completion_tokens')} thought_len={thought_len} source={s.get('source')} tcs={tcs}")

