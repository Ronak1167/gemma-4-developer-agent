import json
import shutil
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_PATH = os.path.join(PROJECT_ROOT, "experiments", "kaggle_smoke_test.ipynb")
DIST_PATH = os.path.join(PROJECT_ROOT, "dist", "kaggle_kernel", "kaggle_smoke_test.ipynb")

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cell 2: Add candidate paths for WHEELHOUSE_DIR
c2_lines = nb["cells"][2]["source"]
new_c2 = []
skip_next = False
for l in c2_lines:
    if "WHEELHOUSE_DIR=Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse')" in l or "WHEELHOUSE_DIR = Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse')" in l:
        new_c2.append("CANDIDATE_WHEELHOUSE_DIRS = [\n")
        new_c2.append("    Path('/kaggle/input/gemma-4-developer-agent-wheelhouse'),\n")
        new_c2.append("    Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse'),\n")
        new_c2.append("    Path('/kaggle/input/metric/gemma-4-developer-agent-wheelhouse'),\n")
        new_c2.append("]\n")
        new_c2.append("WHEELHOUSE_DIR = None\n")
        new_c2.append("for candidate in CANDIDATE_WHEELHOUSE_DIRS:\n")
        new_c2.append("    if candidate.is_dir():\n")
        new_c2.append("        WHEELHOUSE_DIR = candidate\n")
        new_c2.append("        break\n")
        new_c2.append("if WHEELHOUSE_DIR is None and Path('/kaggle/input').is_dir():\n")
        new_c2.append("    for match in Path('/kaggle/input').rglob('*gemma-4-developer-agent-wheelhouse*'):\n")
        new_c2.append("        if match.is_dir():\n")
        new_c2.append("            WHEELHOUSE_DIR = match\n")
        new_c2.append("            break\n")
        new_c2.append("assert WHEELHOUSE_DIR is not None and WHEELHOUSE_DIR.is_dir(), f'Official wheelhouse dataset not mounted in any candidate path: {CANDIDATE_WHEELHOUSE_DIRS}'\n")
    elif "assert WHEELHOUSE_DIR.is_dir()" in l:
        continue
    else:
        new_c2.append(l)
nb["cells"][2]["source"] = new_c2

# Cell 7: Add candidate paths for MODEL_PATH
c7_lines = nb["cells"][7]["source"]
new_c7 = []
for l in c7_lines:
    if 'MODEL_PATH = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")' in l:
        new_c7.append("CANDIDATE_MODEL_PATHS = [\n")
        new_c7.append('    Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2"),\n')
        new_c7.append('    Path(f"/kaggle/input/models/google/gemma-4/Other/{MODEL_NAME}/2"),\n')
        new_c7.append('    Path(f"/kaggle/input/gemma-4/other/{MODEL_NAME}/2"),\n')
        new_c7.append('    Path(f"/kaggle/input/gemma-4/Other/{MODEL_NAME}/2"),\n')
        new_c7.append("]\n")
        new_c7.append("MODEL_PATH = None\n")
        new_c7.append("for candidate in CANDIDATE_MODEL_PATHS:\n")
        new_c7.append("    if candidate.exists():\n")
        new_c7.append("        MODEL_PATH = candidate\n")
        new_c7.append("        break\n")
        new_c7.append('if MODEL_PATH is None and Path("/kaggle/input").is_dir():\n')
        new_c7.append('    for match in Path("/kaggle/input").rglob(f"*{MODEL_NAME}*"):\n')
        new_c7.append("        if match.is_dir():\n")
        new_c7.append("            MODEL_PATH = match\n")
        new_c7.append("            break\n")
        new_c7.append('assert MODEL_PATH is not None and MODEL_PATH.exists(), f"Attached Gemma 4 model input is missing in candidate paths for: {MODEL_NAME}"\n')
    elif "assert MODEL_PATH.exists()" in l:
        continue
    else:
        new_c7.append(l)
nb["cells"][7]["source"] = new_c7

# Ensure gate is False
code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
assert "AUTHORIZE_GPU_SMOKE_TEST = False" in "".join(code_cells[0].get("source", [])), "Gate must be False!"

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

shutil.copy2(NB_PATH, DIST_PATH)
print("Successfully patched experiments and dist notebooks with candidate path resolution!")

