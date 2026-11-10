import hashlib
from pathlib import Path

zip_path = Path("dist/submission-baseline.zip")
expected_zip_hash = "69c4403ee59c581c6e1182272e288af91641e7b3b876e6ecf8cae00329a5bf1b"
if zip_path.exists():
    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"zip hash match: {h == expected_zip_hash} (actual: {h})")
else:
    print("zip does not exist")

