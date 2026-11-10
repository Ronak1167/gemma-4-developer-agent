import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BACKUP_ROOT = ROOT / "reports" / "pre-hash-refresh-backup-2026-11-08"
if BACKUP_ROOT.exists():
    index = 2
    while (ROOT / "reports" / f"pre-hash-refresh-backup-2026-11-08-{index}").exists():
        index += 1
    BACKUP_ROOT = ROOT / "reports" / f"pre-hash-refresh-backup-2026-11-08-{index}"
BACKUP_ROOT.mkdir(parents=True)

backup_files = [
    "dist/submission-final.zip",
    "dist/submission.zip",
    "experiments/kaggle_mini_benchmark.ipynb",
    "scripts/build_competition_submission_kernel.py",
    "scripts/prepare_private_candidate_dataset.py",
    "scripts/prepare_full_benchmark_shards.py",
    "scripts/verify_mini_benchmark_notebook.py",
    "scripts/verify_final_handoff.py",
]
for relative in backup_files:
    source = ROOT / relative
    if source.is_file():
        destination = BACKUP_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

for relative in (
    "dist/kaggle_kernel/kaggle_mini_benchmark.ipynb",
    "dist/kaggle_mini_benchmark/kaggle_mini_benchmark.ipynb",
    "dist/kaggle_mini_benchmark_run/kaggle_mini_benchmark.ipynb",
    "dist/kaggle_competition_submission/gemma4_competition_submission.ipynb",
):
    source = ROOT / relative
    if source.is_file():
        destination = BACKUP_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

print("BACKUP:", BACKUP_ROOT)

def run(script):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)

run("build_final_submission.py")
archive = DIST / "submission-final.zip"
shutil.copy2(archive, DIST / "submission.zip")
archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
source_map = {
    "agent.yaml": ROOT / "agent/agent.yaml",
    "eval_config.yaml": ROOT / "agent/eval_config.yaml",
    "configs/sampling.yaml": ROOT / "agent/configs/sampling.yaml",
    "prompts/system.md": ROOT / "agent/prompts/system.md",
}
source_hashes = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for relative, path in source_map.items()}

mini_path = ROOT / "experiments/kaggle_mini_benchmark.ipynb"
notebook = json.loads(mini_path.read_text(encoding="utf-8"))
updated = False
for cell in notebook["cells"]:
    if cell.get("cell_type") != "code":
        continue
    source = "".join(cell.get("source", []))
    if "EXPECTED_ZIP_SHA256 =" not in source or "EXPECTED_FILE_HASHES =" not in source:
        continue
    source, count = re.subn(
        r'EXPECTED_ZIP_SHA256 = "[0-9a-f]{64}"',
        f'EXPECTED_ZIP_SHA256 = "{archive_hash}"',
        source,
        count=1,
    )
    assert count == 1, "Could not update mini-benchmark archive hash pin"
    for relative, digest in source_hashes.items():
        pattern = r'("' + re.escape(relative) + r'": ")[0-9a-f]{64}(")'
        source, count = re.subn(pattern, lambda match: match.group(1) + digest + match.group(2), source, count=1)
        assert count == 1, f"Could not update mini-benchmark source hash pin: {relative}"
    cell["source"] = source.splitlines(keepends=True)
    updated = True
    break
assert updated, "Mini-benchmark hash pinning cell not found"
notebook_bytes = (json.dumps(notebook, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
mini_path.write_bytes(notebook_bytes)
for relative in (
    "dist/kaggle_kernel/kaggle_mini_benchmark.ipynb",
    "dist/kaggle_mini_benchmark/kaggle_mini_benchmark.ipynb",
    "dist/kaggle_mini_benchmark_run/kaggle_mini_benchmark.ipynb",
):
    (ROOT / relative).write_bytes(notebook_bytes)

run("build_competition_submission_kernel.py")
run("prepare_private_candidate_dataset.py")
run("prepare_full_benchmark_shards.py")

# Move the obsolete retry-run staging directory out of dist without deleting it.
obsolete = DIST / "kaggle_mini_benchmark_retry_run"
if obsolete.exists():
    destination = ROOT / "reports/obsolete-artifacts/kaggle_mini_benchmark_retry_run_2026-11-08"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    shutil.move(str(obsolete), str(destination))
    print("ARCHIVED_OBSOLETE_NOTEBOOK:", destination)

assert (DIST / "submission.zip").read_bytes() == archive.read_bytes()
for relative, path in source_map.items():
    with __import__("zipfile").ZipFile(archive) as zf:
        assert zf.read(relative) == path.read_bytes()
print("REFRESH_COMPLETE")
print("ARCHIVE_SHA256:", archive_hash)
print("ARCHIVE_BYTES:", archive.stat().st_size)
print("SOURCE_HASHES:", json.dumps(source_hashes, sort_keys=True))
print("MINI_NOTEBOOK_SHA256:", hashlib.sha256(notebook_bytes).hexdigest())
