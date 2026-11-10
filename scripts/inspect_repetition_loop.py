import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    trace_file = root / "reports/version-18-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json"
    trace_data = json.loads(trace_file.read_text(encoding="utf-8"))
    steps = trace_data.get("steps", [])

    for s_idx in [35, 36, 37, 38, 39, 40]:
        s = steps[s_idx]
        print(f"--- Step {s_idx} ---")
        if "tool_calls" in s:
            for tc in s["tool_calls"]:
                print("tool_call:", tc.get("function_name"), tc.get("arguments"))
        if "observation" in s:
            print("observation:", s["observation"])

if __name__ == "__main__":
    main()
