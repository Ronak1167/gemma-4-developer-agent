#!/usr/bin/env python3
"""Stages submission-baseline.zip with dataset-metadata.json for Kaggle upload.
Ensures datasets are PRIVATE by default (never passes -u / --public).
"""

import hashlib
import json
import shutil
from pathlib import Path

EXPECTED_SHA256 = "69c4403ee59c581c6e1182272e288af91641e7b3b876e6ecf8cae00329a5bf1b"

def main():
    base_dir = Path(__file__).resolve().parent.parent
    dist_dir = base_dir / "dist"
    source_zip = dist_dir / "submission-baseline.zip"
    stage_dir = dist_dir / "kaggle_dataset"

    assert source_zip.exists(), f"Source archive not found at {source_zip}"

    # Verify source hash
    source_bytes = source_zip.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    assert source_hash == EXPECTED_SHA256, (
        f"Source ZIP SHA-256 mismatch! Got {source_hash}, expected {EXPECTED_SHA256}"
    )

    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_zip = stage_dir / "submission-baseline.zip"
    shutil.copy2(source_zip, staged_zip)

    # Verify staged hash and byte count
    staged_bytes = staged_zip.read_bytes()
    staged_hash = hashlib.sha256(staged_bytes).hexdigest()
    assert staged_hash == EXPECTED_SHA256, (
        f"Staged ZIP SHA-256 mismatch! Got {staged_hash}, expected {EXPECTED_SHA256}"
    )
    assert len(staged_bytes) == len(source_bytes), (
        f"Byte length mismatch: source {len(source_bytes)} vs staged {len(staged_bytes)}"
    )

    metadata = {
        "title": "Gemma 4 Baseline Submission Archive",
        "id": "ronak1167/gemma4-baseline-submission",
        "licenses": [{"name": "other"}],
        "description": (
            "Private competition working artifact for the Google Gemma 4 Developer Agent Competition on Kaggle. "
            "Contains the declarative Phase 2.1 baseline SWE agent submission bundle (submission-baseline.zip). "
            "This dataset is a private competition working artifact and is not intended for public redistribution. "
            "No additional license is granted through this dataset. "
            "Third-party components and dependencies retain their respective upstream licenses."
        )
    }

    metadata_path = stage_dir / "dataset-metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("=== Kaggle Dataset Staging Successful ===")
    print(f"  Source ZIP: {source_zip} ({len(source_bytes)} bytes)")
    print(f"  Staged ZIP: {staged_zip} ({len(staged_bytes)} bytes)")
    print(f"  Verified SHA-256: {staged_hash}")
    print(f"  Metadata file: {metadata_path}")
    print(f"  Target Dataset Slug: {metadata['id']}")
    print(f"  Expected Notebook Mount Path: /kaggle/input/gemma4-baseline-submission/submission-baseline.zip")
    print("\n--- Kaggle Creation Commands ---")
    print("PRIVATE Dataset Creation (Default - DO NOT USE -u):")
    print("  python -m kaggle datasets create -p dist/kaggle_dataset")
    print("\nOr upload dist/submission-baseline.zip via Kaggle UI as a PRIVATE dataset titled 'gemma4-baseline-submission'.")

if __name__ == "__main__":
    main()
