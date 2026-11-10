import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
FOLDER = DIST / "kaggle_competition_submission"
FOLDER.mkdir(parents=True, exist_ok=True)
ARCHIVE = DIST / "submission-final.zip"
ARCHIVE_HASH = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
SOURCE_HASHES = {
    "agent.yaml": hashlib.sha256((ROOT / "agent/agent.yaml").read_bytes()).hexdigest(),
    "eval_config.yaml": hashlib.sha256((ROOT / "agent/eval_config.yaml").read_bytes()).hexdigest(),
    "configs/sampling.yaml": hashlib.sha256((ROOT / "agent/configs/sampling.yaml").read_bytes()).hexdigest(),
    "prompts/system.md": hashlib.sha256((ROOT / "agent/prompts/system.md").read_bytes()).hexdigest(),
}

code = r'''from pathlib import Path
import hashlib
import shutil
import zipfile

SOURCE_ROOT = Path('/kaggle/input/datasets/ronak1167/gemma4-optimized-candidate')
SOURCE_ARCHIVE = SOURCE_ROOT / 'submission-final.zip'
OUTPUT = Path('/kaggle/working/submission.zip')
EXPECTED_ZIP_HASHES = {'__ARCHIVE_HASH__', 'bd22384a9f1c94275644d2b9e15909f4ac9f566ddc7dfd24fb42fcab5c183437'}
EXPECTED_FILES = {
    'agent.yaml': '__HASH_AGENT__',
    'eval_config.yaml': '__HASH_EVAL__',
    'configs/sampling.yaml': '__HASH_SAMPLING__',
    'prompts/system.md': '__HASH_PROMPT__',
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def verify_archive(path):
    archive_bytes = path.read_bytes()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    assert archive_hash in EXPECTED_ZIP_HASHES, f'Candidate archive hash mismatch: {archive_hash}'
    with zipfile.ZipFile(path, 'r') as zf:
        assert zf.testzip() is None, 'Candidate archive CRC validation failed'
        names = zf.namelist()
        assert names == list(EXPECTED_FILES), f'Unexpected archive entries/order: {names}'
        assert len(names) == len(set(names)), 'Duplicate archive entries detected'
        for relative, expected_hash in EXPECTED_FILES.items():
            actual_hash = hashlib.sha256(zf.read(relative)).hexdigest()
            assert actual_hash == expected_hash, f'Source hash mismatch for {relative}: {actual_hash}'
        unpacked = sum(info.file_size for info in zf.infolist())
        assert unpacked < 3 * 1024**3, f'Unpacked archive too large: {unpacked}'
    return archive_bytes, archive_hash, unpacked

if SOURCE_ARCHIVE.is_file():
    archive_bytes, archive_hash, unpacked = verify_archive(SOURCE_ARCHIVE)
    shutil.copyfile(SOURCE_ARCHIVE, OUTPUT)
    print('INPUT_MODE: pinned submission-final.zip')
else:
    for relative, expected_hash in EXPECTED_FILES.items():
        source = SOURCE_ROOT / relative
        assert source.is_file(), f'Missing candidate source file: {source}'
        actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f'Source hash mismatch for {relative}: {actual_hash}'
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w') as zf:
        for relative in EXPECTED_FILES:
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0
            zf.writestr(info, (SOURCE_ROOT / relative).read_bytes(),
                        compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    archive_bytes, archive_hash, unpacked = verify_archive(OUTPUT)
    print('INPUT_MODE: hash-verified unpacked source files')

assert OUTPUT.is_file() and OUTPUT.read_bytes() == archive_bytes
assert archive_hash in EXPECTED_ZIP_HASHES
print('SUBMISSION_ARCHIVE:', OUTPUT)
print('ARCHIVE_BYTES:', OUTPUT.stat().st_size)
print('UNPACKED_BYTES:', unpacked)
print('SHA256:', archive_hash)
print('SOURCE_HASHES: ALL MATCH')
print('ZIP_VALIDATION: PASS')
'''
for key, placeholder in (
    ("agent.yaml", "__HASH_AGENT__"),
    ("eval_config.yaml", "__HASH_EVAL__"),
    ("configs/sampling.yaml", "__HASH_SAMPLING__"),
    ("prompts/system.md", "__HASH_PROMPT__"),
):
    code = code.replace(placeholder, SOURCE_HASHES[key])
code = code.replace("__ARCHIVE_HASH__", ARCHIVE_HASH)

cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Gemma 4 Developer Agent — Competition Submission\n",
            "\n",
            "This notebook creates submission.zip from the pinned private candidate dataset.\n",
            "It accepts either the canonical ZIP or the four unpacked source files, verifies all hashes, and produces the exact deterministic archive.\n",
            "The competition scoring harness evaluates the declarative agent on hidden tasks.\n",
        ],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.splitlines()],
    },
]
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
notebook_name = "gemma4_competition_submission.ipynb"
(FOLDER / notebook_name).write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

metadata = {
    "id": "ronak1167/gemma-4-swe-agent-final-submission",
    "title": "Gemma 4 SWE Agent Final Submission",
    "code_file": notebook_name,
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "enable_tpu": False,
    "machine_shape": "NvidiaL4",
    "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    "enable_internet": False,
    "dataset_sources": ["ronak1167/gemma4-optimized-candidate"],
    "competition_sources": ["gemma-4-developer-agent"],
    "kernel_sources": [],
    "model_sources": ["google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2"],
}
(FOLDER / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print("CREATED:", FOLDER)
print("KERNEL_SLUG:", metadata["id"])
print("ARCHIVE_SHA256:", ARCHIVE_HASH)
print("SOURCE_HASHES:", json.dumps(SOURCE_HASHES, sort_keys=True))
