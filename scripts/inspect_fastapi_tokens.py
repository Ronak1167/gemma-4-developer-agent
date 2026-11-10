import json
from pathlib import Path

trace = json.loads(Path('reports/gpu-diagnostic-v22-output/results/mini_benchmark/traces/trace_fastapi_15589.json').read_text(encoding='utf-8'))
for i, s in enumerate(trace['steps']):
    m = s.get('metrics') or s.get('extra', {}).get('usage') or {}
    tcs = [t.get('function_name') or t.get('name') for t in (s.get('tool_calls') or [])]
    print(f"Step {i:2d}: pt={m.get('prompt_tokens')} ct={m.get('completion_tokens')} source={s.get('source')} tcs={tcs}")

