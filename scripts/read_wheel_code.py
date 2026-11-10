import zipfile
from pathlib import Path

def read_file_from_wheel(wheel_name, file_name):
    whl_path = Path("reports/wheelhouse-inspect") / wheel_name
    with zipfile.ZipFile(whl_path, "r") as z:
        return z.read(file_name).decode("utf-8")

# Let's inspect adk_submission/paths.py and adk_submission/server.py
paths_py = read_file_from_wheel("adk_submission-0.2.13-py3-none-any.whl", "adk_submission/paths.py")
print("=== adk_submission/paths.py ===")
print(paths_py[:1500])

server_py = read_file_from_wheel("adk_submission-0.2.13-py3-none-any.whl", "adk_submission/server.py")
print("\n=== adk_submission/server.py ===")
print(server_py[:2000])

