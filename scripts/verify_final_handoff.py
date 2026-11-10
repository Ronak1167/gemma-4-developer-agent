import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "dist/submission-final.zip"
SOURCES = {
    "agent.yaml": ROOT / "agent/agent.yaml",
    "eval_config.yaml": ROOT / "agent/eval_config.yaml",
    "configs/sampling.yaml": ROOT / "agent/configs/sampling.yaml",
    "prompts/system.md": ROOT / "agent/prompts/system.md",
}
digest = lambda data: hashlib.sha256(data).hexdigest()

assert ARCHIVE.is_file()
archive_bytes = ARCHIVE.read_bytes()
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    assert archive.namelist() == list(SOURCES)
    assert len(archive.namelist()) == len(set(archive.namelist()))
    unpacked = sum(info.file_size for info in archive.infolist())
    assert unpacked < 3 * 1024**3
    content = []
    for relative, source in SOURCES.items():
        payload = archive.read(relative)
        assert payload == source.read_bytes(), f"Archive/source mismatch: {relative}"
        print(f"[PASS] {relative}: {len(payload)} bytes; SHA-256 {digest(payload)}")
        content.append(payload.decode("utf-8"))
    combined = "\n".join(content)

for forbidden in ("ronak1167", "Ronak Jain", "rich_4077", "rich_3944", "fastapi_15589", "requests_7502"):
    assert forbidden.lower() not in combined.lower(), f"Task/user-specific hardcoding: {forbidden}"
for pattern in (r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"AKIA[0-9A-Z]{16}",
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", r"sk-[A-Za-z0-9]{24,}"):
    assert not re.search(pattern, combined), f"Credential-like pattern found: {pattern}"

assert (ROOT / "dist/submission.zip").read_bytes() == archive_bytes
assert (ROOT / "dist/submission-baseline.zip").is_file()
assert digest((ROOT / "dist/submission-baseline.zip").read_bytes()) == "69c4403ee59c581c6e1182272e288af91641e7b3b876e6ecf8cae00329a5bf1b"

manifest = [json.loads(line) for line in (ROOT / "starter/official/tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
task_ids = [task["instance_id"] for task in manifest]
assert len(manifest) == 129 and len(set(task_ids)) == 129
plan = json.loads((ROOT / "reports/benchmark-shards.json").read_text(encoding="utf-8"))
flattened = [task_id for shard in plan["shards"] for task_id in shard["task_ids"]]
assert len(flattened) == 129 and len(set(flattened)) == 129 and set(flattened) == set(task_ids)
assert [shard["task_count"] for shard in plan["shards"]] == [32, 33, 32, 32]

for script in ("verify_phase6_local.py", "test_pre_retry_paths.py"):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)

print("[PASS] final archive is source-identical, CRC-valid, safe, and credential-screened")
print("[PASS] deterministic baseline archive remains unchanged")
print("[PASS] all 129 official public task IDs are unique and partitioned exactly once")
print("[PASS] final local validation suites passed")
print("FINAL_ARCHIVE_SHA256=" + digest(archive_bytes))
print("FINAL_ARCHIVE_BYTES=" + str(len(archive_bytes)))
print("UNPACKED_BYTES=" + str(unpacked))
