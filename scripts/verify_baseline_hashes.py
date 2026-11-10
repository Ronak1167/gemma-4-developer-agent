import hashlib
from pathlib import Path

files = {
    "agent.yaml": Path("agent/agent.yaml"),
    "configs/sampling.yaml": Path("agent/configs/sampling.yaml"),
    "prompts/system.md": Path("agent/prompts/system.md"),
}

EXPECTED_FILE_HASHES = {
    "agent.yaml": "2949364aec51a49ab9288a1f7c18cfca7d65e275bd31d26d98d4f0331e8f6c6b",
    "configs/sampling.yaml": "a0309e72890242fbb3ff0620ae802dd3d8b3492a15493b6ee279be06bcfb5cdc",
    "prompts/system.md": "ff2a36226962d493fda697a5cb781061ed9ec53ca08df90a5f3962d953fd4942",
}

for name, p in files.items():
    data = p.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    exp = EXPECTED_FILE_HASHES[name]
    print(f"{name}: {h == exp} (actual: {h}, expected: {exp})")

