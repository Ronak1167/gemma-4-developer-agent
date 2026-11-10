import zipfile
from pathlib import Path

whl_path = Path("reports/wheelhouse-inspect/adk_submission-0.2.13-py3-none-any.whl")
with zipfile.ZipFile(whl_path, "r") as z:
    code = z.read("adk_submission/server.py").decode("utf-8")

lines = code.splitlines()
for i, line in enumerate(lines):
    if "def create_model_registry" in line:
        print("\n".join(lines[i:i+60]))
        break

