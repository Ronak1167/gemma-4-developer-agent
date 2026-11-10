import json

with open("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json", "r", encoding="utf-8") as f:
    trace = json.load(f)

steps = trace.get("steps", [])

with open("reports/trajectory_chronology.txt", "w", encoding="utf-8") as out:
    tool_call_num = 0
    for i, step in enumerate(steps):
        tcs = step.get("tool_calls", [])
        msg = step.get("message", "")
        obs = step.get("observation", {})
        obs_content = obs.get("content", "")
        
        if tcs:
            tool_call_num += 1
            tc = tcs[0]
            func_name = tc.get("function_name")
            args = tc.get("arguments", {})
            out.write(f"\n{'='*70}\n")
            out.write(f"TOOL CALL #{tool_call_num} (Step {i})\n")
            out.write(f"Tool: {func_name}\n")
            out.write(f"Arguments: {json.dumps(args, indent=2)}\n")
            out.write(f"--- Model Thinking Before Tool Call ---\n{msg.strip()}\n")
            out.write(f"--- Observation ---\n{obs_content[:600]}\n")
            if len(obs_content) > 600:
                out.write(f"... [truncated {len(obs_content)-600} chars]\n")
        else:
            if msg:
                out.write(f"\n[Non-Tool Message at Step {i}]:\n{msg[:400]}\n")

print(f"Reconstructed {tool_call_num} tool calls into reports/trajectory_chronology.txt")

