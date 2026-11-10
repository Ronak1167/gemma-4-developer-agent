import hashlib
import zipfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    target = root / "dist" / "submission-final.zip"
    files = [
        ("agent.yaml", root / "agent" / "agent.yaml"),
        ("eval_config.yaml", root / "agent" / "eval_config.yaml"),
        ("configs/sampling.yaml", root / "agent" / "configs" / "sampling.yaml"),
        ("prompts/system.md", root / "agent" / "prompts" / "system.md"),
    ]
    for _, path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    with zipfile.ZipFile(target, "w") as zf:
        for arcname, path in files:
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = target.read_bytes()
    with zipfile.ZipFile(target) as zf:
        assert zf.testzip() is None
        assert zf.namelist() == [name for name, _ in files]
        for name, path in files:
            assert zf.read(name) == path.read_bytes()
    print(f"Archive: {target}")
    print(f"Size: {len(data)} bytes")
    print(f"SHA-256: {hashlib.sha256(data).hexdigest()}")
    print("Deterministic archive build and source-byte comparison passed.")


if __name__ == "__main__":
    main()
