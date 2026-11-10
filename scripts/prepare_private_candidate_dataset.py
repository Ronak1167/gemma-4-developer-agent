import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SLUG = "ronak1167/gemma4-optimized-candidate"
ARCHIVE = DIST / "submission-final.zip"
SOURCE_MAP = {
    "agent.yaml": ROOT / "agent/agent.yaml",
    "eval_config.yaml": ROOT / "agent/eval_config.yaml",
    "configs/sampling.yaml": ROOT / "agent/configs/sampling.yaml",
    "prompts/system.md": ROOT / "agent/prompts/system.md",
}
metadata = {
    "title": "Gemma 4 Optimized Candidate Submission",
    "id": SLUG,
    "licenses": [{"name": "other"}],
    "description": (
        "Private working artifact for the Google Gemma 4 Developer Agent Competition. "
        "Contains the deterministic, integrity-pinned submission archive. "
        "The archive contains the four required agent source files at their exact relative paths. "
        "This dataset is not intended for public redistribution. Third-party components retain their upstream licenses."
    ),
}

# The Kaggle CLI skips nested directories by default. Keep the upload payload flat
# and make the archive the single source of truth; the notebook validates its contents.
upload = DIST / "kaggle_dataset_optimized_upload"
if upload.exists():
    shutil.rmtree(upload)
upload.mkdir(parents=True)
(upload / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
shutil.copy2(ARCHIVE, upload / "submission-final.zip")
assert sorted(p.name for p in upload.iterdir()) == ["dataset-metadata.json", "submission-final.zip"]

# Keep a richer local staging directory for inspection and byte-for-byte checks.
stage = DIST / "kaggle_dataset_final"
stage.mkdir(parents=True, exist_ok=True)
(stage / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
for relative, source in SOURCE_MAP.items():
    destination = stage / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
shutil.copy2(ARCHIVE, stage / "submission-final.zip")

for relative, source in SOURCE_MAP.items():
    assert (stage / relative).read_bytes() == source.read_bytes()
assert (stage / "submission-final.zip").read_bytes() == ARCHIVE.read_bytes()

for folder in (DIST / "kaggle_mini_benchmark", DIST / "kaggle_mini_benchmark_run"):
    metadata_path = folder / "kernel-metadata.json"
    kernel_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    kernel_metadata["dataset_sources"] = [
        SLUG,
        "metric/gemma-4-developer-agent-wheelhouse",
    ]
    metadata_path.write_text(json.dumps(kernel_metadata, indent=2) + "\n", encoding="utf-8")

print("PRIVATE_DATASET_SLUG:", SLUG)
print("UPLOAD_FILES:", sorted(p.name for p in upload.iterdir()))
print("UPLOAD_ARCHIVE_BYTES:", (upload / "submission-final.zip").stat().st_size)
print("LOCAL_SOURCE_FILES_AND_ARCHIVE: ALL MATCH")
