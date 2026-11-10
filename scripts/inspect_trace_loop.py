import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    trace_file = root / "reports/version-18-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json"
    trace_data = json.loads(trace_file.read_text(encoding="utf-8"))
    steps = trace_data.get("steps", [])

    for s_idx in [11, 12, 13, 14, 17, 25, 36, 37, 40, 42, 47, 48]:
        if s_idx < len(steps):
            s = steps[s_idx]
            tc = s.get("tool_calls", [{}])[0]
            obs = s.get("observation", {})
            print(f"=== Step {s_idx} ===")
            print(f"Thought: {s.get('thought', '')[:120]}...")
            print(f"Tool: {tc.get('function_name')} -> {tc.get('arguments')}")
            obs_out = obs.get("output") or obs.get("stdout") or str(obs)[:120]
            print(f"Obs: {str(obs_out)[:120]}")

if __name__ == "__main__":
    main()

