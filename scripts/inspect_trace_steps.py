import json
from pathlib import Path

trace_path = Path("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json")
with open(trace_path, "r", encoding="utf-8") as f:
    trace = json.load(f)

print("Final metrics:")
print(json.dumps(trace.get("final_metrics"), indent=2))

steps = trace.get("steps", [])
print(f"\nTotal steps: {len(steps)}")
for i, step in enumerate(steps):
    step_id = step.get("step_id", i)
    tool_calls = step.get("tool_calls", [])
    observation = step.get("observation", {})
    model_output = step.get("model_output", {})
    print(f"\n--- Step {i} ---")
    if "thought" in model_output:
        print(f"Thought: {str(model_output['thought'])[:150]}...")
    if tool_calls:
        for tc in tool_calls:
            print(f"Tool Call: {tc.get('name')} | args: {str(tc.get('arguments'))[:120]}")
    elif "tool" in step:
        print(f"Tool: {step['tool']}")
    else:
        print(f"Step keys: {list(step.keys())}")
        if "tools" in step:
            print(f"Tools: {step['tools']}")
        if "action" in step:
            print(f"Action: {step['action']}")

