import json
from pathlib import Path

trace_path = Path("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json")
with open(trace_path, "r", encoding="utf-8") as f:
    trace = json.load(f)

steps = trace.get("steps", [])
print(f"Total steps: {len(steps)}")

with open("reports/trace_detailed_dump.txt", "w", encoding="utf-8") as out:
    for i, step in enumerate(steps):
        out.write(f"\n{'='*60}\nSTEP {i} (step_id: {step.get('step_id')}, source: {step.get('source')})\n{'='*60}\n")
        msg = step.get("message", {})
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
            thought = msg.get("thought", msg.get("reasoning_content"))
            tool_calls = msg.get("tool_calls", [])
            out.write(f"Role: {role}\n")
            if thought:
                out.write(f"--- Thought ---\n{thought}\n")
            if content:
                out.write(f"--- Content ---\n{content}\n")
            if tool_calls:
                out.write(f"--- Tool Calls ---\n")
                for tc in tool_calls:
                    func = tc.get("function", {})
                    out.write(f"  Tool: {func.get('name')}\n  Args: {func.get('arguments')}\n")
        elif isinstance(msg, str):
            out.write(f"Message: {msg}\n")
        
        # Check observation or tool results
        extra = step.get("extra", {})
        if extra:
            out.write(f"--- Extra ---\n{json.dumps(extra, indent=2)[:500]}\n")

print("Dumped detailed trace to reports/trace_detailed_dump.txt")

