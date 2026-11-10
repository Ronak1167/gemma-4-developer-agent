import json
from collections import Counter
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    trace_file = root / "reports/version-18-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json"
    trace_data = json.loads(trace_file.read_text(encoding="utf-8"))
    
    steps = trace_data.get("steps", [])
    tool_sequence = []
    tool_names = Counter()

    for i, s in enumerate(steps):
        for tc in s.get("tool_calls", []):
            name = tc.get("function_name")
            args = tc.get("arguments", {})
            tool_names[name] += 1
            tool_sequence.append((i, name, args))

    print(f"Total tool calls: {len(tool_sequence)}")
    print("\nTool counts:")
    for n, c in tool_names.most_common():
        print(f"  {n}: {c}")

    print("\nComplete tool call sequence:")
    for step_num, name, args in tool_sequence:
        if name == "run_command":
            arg_str = args.get("command", "")
            # truncate long commands
            if len(arg_str) > 70:
                arg_str = arg_str[:70] + "..."
            print(f"  Step {step_num:2d} [run_command]: {arg_str}")
        elif name == "read_file":
            print(f"  Step {step_num:2d} [read_file]: {args.get('filepath')} (start={args.get('start_line')})")
        elif name == "edit_file":
            print(f"  Step {step_num:2d} [edit_file]: {args.get('filepath')}")
        elif name == "submit_patch":
            print(f"  Step {step_num:2d} [submit_patch]: (no args)")
        else:
            print(f"  Step {step_num:2d} [{name}]: {str(args)[:60]}")

if __name__ == "__main__":
    main()
