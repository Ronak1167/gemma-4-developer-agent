import json

with open("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json", "r", encoding="utf-8") as f:
    trace = json.load(f)

steps = trace.get("steps", [])
for i, step in enumerate(steps):
    extra = step.get("extra", {})
    ev_type = extra.get("event_type")
    msg = step.get("message", {})
    if ev_type == "tool_result":
        print(f"\n=== Step {i} Tool Result ===")
        print(f"Tool: {extra.get('tool_name')}")
        content = msg.get("content") if isinstance(msg, dict) else str(msg)
        print(f"Content:\n{content[:600]}")

