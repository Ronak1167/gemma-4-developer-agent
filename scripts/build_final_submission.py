import hashlib
import shutil
import zipfile
from pathlib import Path


def create_deterministic_zip(target: Path, files: list[tuple[str, Path]]):
    target.parent.mkdir(parents=True, exist_ok=True)
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
    return hashlib.sha256(data).hexdigest(), len(data)


def main():
    root = Path(__file__).resolve().parent.parent
    dist = root / "dist"
    files = [
        ("agent.yaml", root / "agent" / "agent.yaml"),
        ("eval_config.yaml", root / "agent" / "eval_config.yaml"),
        ("configs/sampling.yaml", root / "agent" / "configs" / "sampling.yaml"),
        ("prompts/system.md", root / "agent" / "prompts" / "system.md"),
    ]
    for _, path in files:
        if not path.is_file():
            raise FileNotFoundError(path)

    targets = [
        dist / "submission-final.zip",
        dist / "submission.zip",
        dist / "submission-v30.zip",
        dist / "kaggle_dataset_optimized_upload" / "submission-final.zip",
        dist / "kaggle_dataset_final" / "submission-final.zip",
    ]

    for target in targets:
        digest, size = create_deterministic_zip(target, files)
        print(f"Archive: {target.name} ({size} bytes, SHA-256: {digest[:16]}...)")

    # Also update unpacked source files in datasets
    for ds_folder in ["kaggle_dataset_optimized_upload", "kaggle_dataset_final"]:
        dest = dist / ds_folder
        if dest.is_dir():
            for arcname, src_path in files:
                out_path = dest / arcname
                out_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_path, out_path)

    print("All candidate v30 archives and datasets synchronized successfully.")


if __name__ == "__main__":
    main()
