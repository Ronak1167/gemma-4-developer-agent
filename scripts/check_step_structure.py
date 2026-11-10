import json

with open("reports/version-10-smoke-test-output/results/smoke_test/traces/trace_rich_4077.json", "r", encoding="utf-8") as f:
    trace = json.load(f)

step4 = trace["steps"][4]
print("=== Step 4 ===")
print(json.dumps(step4, indent=2)[:1500])

step5 = trace["steps"][5]
print("\n=== Step 5 ===")
print(json.dumps(step5, indent=2)[:1500])

