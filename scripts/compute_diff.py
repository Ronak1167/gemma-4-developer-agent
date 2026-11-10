import difflib
import json
from pathlib import Path

# Compare reports/all_notebook_cells.py (which was dumped before our patch) with current notebook
with open("reports/all_notebook_cells.py", "r", encoding="utf-8") as f:
    old_dump = f.read()

with open("experiments/kaggle_smoke_test.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

new_cells_dump = []
for i, cell in enumerate(nb["cells"]):
    new_cells_dump.append(f"\n{'='*40}\n# CELL {i} ({cell['cell_type']})\n{'='*40}\n")
    new_cells_dump.append("".join(cell["source"]))
    new_cells_dump.append("\n")
new_dump = "".join(new_cells_dump)

diff = difflib.unified_diff(
    old_dump.splitlines(),
    new_dump.splitlines(),
    fromfile="Notebook (Version 9 State)",
    tofile="Notebook (Audited Version 10 Ready State)",
    lineterm="",
)
diff_lines = list(diff)
print(f"Total diff lines: {len(diff_lines)}")
with open("reports/notebook_diff.patch", "w", encoding="utf-8") as f:
    f.write("\n".join(diff_lines))
print("Wrote reports/notebook_diff.patch successfully.")
for line in diff_lines[:60]:
    print(line)

