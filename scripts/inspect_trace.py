import json
from pathlib import Path

trace_path = Path("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json")
with open(trace_path, "r", encoding="utf-8") as f:
    trace = json.load(f)

print(f"Trace keys: {list(trace.keys())}")
events = trace.get("events", trace.get("steps", trace.get("trajectory", [])))
if isinstance(trace, list):
    events = trace

print(f"Total events/steps in trace: {len(events) if isinstance(events, list) else type(events)}")

# If events is a list, let's inspect the types of events and tool calls
if isinstance(events, list):
    tool_calls_seen = []
    for i, step in enumerate(events):
        event_type = step.get("type", step.get("event", "unknown"))
        tool_name = step.get("tool_name", step.get("action", {}).get("tool", step.get("name")))
        if tool_name:
            tool_calls_seen.append((i, tool_name, step.get("input", step.get("args"))))
    print(f"Discovered {len(tool_calls_seen)} tool calls:")
    for idx, name, args in tool_calls_seen[:25]:
        print(f"  Step {idx}: {name} -> {str(args)[:120]}")
else:
    # Print preview of trace structure
    print(json.dumps(trace, indent=2)[:1500])

