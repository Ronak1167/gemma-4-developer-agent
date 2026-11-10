import json
from pathlib import Path

trace_path = Path("reports/gpu-diagnostic-v22-output/results/mini_benchmark/traces/trace_fastapi_15589.json")
data = json.loads(trace_path.read_text(encoding="utf-8"))

steps = data.get("steps", [])
print(f"Total steps: {len(steps)}")

for i, s in enumerate(steps):
    msg = s.get("message", {})
    obs = s.get("observation", "")
    llm_count = s.get("llm_call_count")
    # check prompt length or tokens if recorded
    print(f"Step {i}:")
    print(f"  source: {s.get('source')}, step_id: {s.get('step_id')}")
    if isinstance(msg, dict):
        role = msg.get("role")
        thought = msg.get("thought") or msg.get("reasoning_content")
        tool_calls = msg.get("tool_calls")
        content = msg.get("content")
        print(f"  role: {role}, tool_calls: {len(tool_calls) if tool_calls else 0}, thought_len: {len(str(thought)) if thought else 0}, content_len: {len(str(content)) if content else 0}")
        if tool_calls:
            for tc in tool_calls:
                func = tc.get("function") or {}
                print(f"    call: {func.get('name')} {func.get('arguments')}")
    if obs:
        print(f"  observation length: {len(str(obs))}")
        if len(str(obs)) > 2000:
            print(f"    obs snippet: {str(obs)[:200]} ... {str(obs)[-200:]}")
    extra = s.get("extra", {})
    if extra:
        print(f"  extra keys: {list(extra.keys())}")
        if "usage" in extra:
            print(f"  usage: {extra['usage']}")

