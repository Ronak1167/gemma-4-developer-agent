import zipfile
from pathlib import Path

wheel_dir = Path("reports/wheelhouse-inspect")
for whl_path in wheel_dir.glob("*.whl"):
    with zipfile.ZipFile(whl_path, "r") as z:
        print(f"\n=== Wheel: {whl_path.name} ===")
        for name in z.namelist():
            if name.endswith(".py"):
                print(f"  {name}")
