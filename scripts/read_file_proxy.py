import tarfile
from pathlib import Path

snapshot_path = Path("starter/official/snapshots/rich_4077.tgz")
if snapshot_path.exists():
    with tarfile.open(snapshot_path, "r:gz") as tar:
        for member in tar.getmembers():
            if "file_proxy.py" in member.name:
                print("Found:", member.name)
                f = tar.extractfile(member)
                if f:
                    content = f.read().decode("utf-8")
                    print(content)
                break
else:
    print("Snapshot not found at", snapshot_path)

