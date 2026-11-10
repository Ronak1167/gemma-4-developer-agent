import json
from pathlib import Path

traces_dir = Path("reports/gpu-diagnostic-v22-output/results/mini_benchmark/traces")
for p in traces_dir.glob("trace_*.json"):
    data = json.loads(p.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    print(f"\n==========================================")
    print(f"=== {p.name} (Steps: {len(steps)}) ===")
    print(f"==========================================")
    total_obs_chars = 0
    for i, s in enumerate(steps):
        tool_calls = s.get("tool_calls", []) or []
        obs = s.get("observation", "")
        if isinstance(obs, dict):
            obs = json.dumps(obs)
        total_obs_chars += len(str(obs))
        tc_names = [tc.get("name") or (tc.get("function") or {}).get("name") for tc in tool_calls]
        tc_args = [tc.get("arguments") or tc.get("args") or (tc.get("function") or {}).get("arguments") for tc in tool_calls]
        step_err = s.get("error")
        print(f"Step {i:2d}: calls={tc_names} | obs_len={len(str(obs))} | cum_obs={total_obs_chars} | err={bool(step_err)}")
        for n, a in zip(tc_names, tc_args):
            print(f"   -> {n}: {str(a)[:150]}")
        if step_err:
            print(f"   ERROR: {str(step_err)[:200]}")

