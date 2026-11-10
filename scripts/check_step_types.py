import json

with open("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json", "r", encoding="utf-8") as f:
    trace = json.load(f)

steps = trace.get("steps", [])
for i, step in enumerate(steps):
    extra = step.get("extra", {})
    source = step.get("source")
    role = step.get("message", {}).get("role") if isinstance(step.get("message"), dict) else None
    print(f"Step {i}: source={source}, role={role}, extra_keys={list(extra.keys())}, event_type={extra.get('event_type')}")

