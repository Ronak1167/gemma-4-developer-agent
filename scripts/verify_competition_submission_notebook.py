import ast
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "dist/kaggle_competition_submission"
NOTEBOOK = FOLDER / "gemma4_competition_submission.ipynb"
METADATA = FOLDER / "kernel-metadata.json"
ARCHIVE = ROOT / "dist/submission-final.zip"
SOURCE_MAP = {
    "agent.yaml": ROOT / "agent/agent.yaml",
    "eval_config.yaml": ROOT / "agent/eval_config.yaml",
    "configs/sampling.yaml": ROOT / "agent/configs/sampling.yaml",
    "prompts/system.md": ROOT / "agent/prompts/system.md",
}
archive_hash = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
assert len(cells) == 1, f"Expected one packaging cell, found {len(cells)}"
cell = cells[0]
source = "".join(cell.get("source", []))
ast.parse(source)
assert cell.get("execution_count") is None and cell.get("outputs") == []
assert "AUTHORIZE_GPU" not in source
assert archive_hash in source, "Competition notebook archive hash pin is stale"
for relative, path in SOURCE_MAP.items():
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest in source, f"Competition notebook source hash pin stale: {relative}"

metadata = json.loads(METADATA.read_text(encoding="utf-8"))
assert metadata["id"] == "ronak1167/gemma-4-swe-agent-final-submission"
assert metadata["code_file"] == NOTEBOOK.name
assert metadata["is_private"] is True and metadata["enable_gpu"] is True
assert metadata["enable_internet"] is False and metadata["machine_shape"] == "NvidiaL4"
assert metadata["dataset_sources"] == ["ronak1167/gemma4-optimized-candidate"]
assert metadata["competition_sources"] == ["gemma-4-developer-agent"]

def run_notebook(input_root, output, include_archive):
    input_root.mkdir(parents=True, exist_ok=True)
    if include_archive:
        shutil.copy2(ARCHIVE, input_root / "submission-final.zip")
    else:
        for relative, path in SOURCE_MAP.items():
            target = input_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    runnable = source.replace(
        "Path('/kaggle/input/datasets/ronak1167/gemma4-optimized-candidate')",
        f"Path({str(input_root)!r})",
    ).replace(
        "Path('/kaggle/working/submission.zip')",
        f"Path({str(output)!r})",
    )
    assert runnable != source, "Dry-run path substitution failed"
    exec(compile(runnable, str(NOTEBOOK), "exec"), {"__name__": "__main__"})
    assert output.is_file() and output.read_bytes() == ARCHIVE.read_bytes()
    with zipfile.ZipFile(output) as zf:
        assert zf.testzip() is None and zf.namelist() == list(SOURCE_MAP)
        for relative, path in SOURCE_MAP.items():
            assert zf.read(relative) == path.read_bytes()

with tempfile.TemporaryDirectory(prefix="gemma4_submission_dryrun_") as temp:
    root = Path(temp)
    run_notebook(root / "unpacked_input", root / "unpacked_working" / "submission.zip", False)
    print("[PASS] unpacked-source Kaggle dataset layout")
    run_notebook(root / "archive_input", root / "archive_working" / "submission.zip", True)
    print("[PASS] ZIP-only Kaggle dataset layout")
print("[PASS] both dataset layouts produce the exact canonical deterministic archive")
print("[PASS] competition notebook syntax, metadata, private/offline configuration, and source pins")
