import zipfile
from pathlib import Path

whl_path = Path("reports/wheelhouse-inspect/adk_submission-0.2.13-py3-none-any.whl")
with zipfile.ZipFile(whl_path, "r") as z:
    code = z.read("adk_submission/server.py").decode("utf-8")

lines = code.splitlines()
start = 0
for i, line in enumerate(lines):
    if "class VllmConfig" in line or "class VllmServer" in line:
        print(f"Line {i}: {line}")

for i, line in enumerate(lines):
    if "class VllmServer" in line:
        print("\n".join(lines[i:i+120]))
        break

