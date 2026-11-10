import json
from collections import Counter
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    trace_root = root / "reports/version-3-mini-benchmark-output/results/mini_benchmark/traces"
    traces = sorted(trace_root.glob("*.json"))
    if not traces:
        raise SystemExit("No mini-benchmark trace files found; collect the Kaggle outputs first.")
    report = ["# Mini-Benchmark Trace Efficiency Audit", ""]
    for path in traces:
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = data.get("steps", [])
        calls = [c for s in steps for c in s.get("tool_calls", [])]
        counts = Counter(c.get("function_name") for c in calls)
        run_commands = []
        for step in steps:
            for call in step.get("tool_calls", []):
                if call.get("function_name") == "run_command":
                    run_commands.append((step.get("step_id"), json.dumps(call.get("arguments", {}), sort_keys=True)))
        repeated = Counter(x[1] for x in run_commands)
        redundant = sum(n - 1 for n in repeated.values() if n > 1)
        report += [
            f"## {path.stem}",
            f"- Trace steps: {len(steps)}",
            f"- Tool calls: {len(calls)}",
            f"- Tool distribution: {dict(counts)}",
            f"- run_command calls: {len(run_commands)}; unique commands: {len(repeated)}",
            f"- Redundant identical run_command repeats beyond first use: {redundant}",
        ]
        for command, n in repeated.most_common(5):
            if n > 1:
                report.append(f"- Repeated {n} times: {command[:260]}")
        report.append("")
    out = root / "reports/mini-benchmark-trace-analysis.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
