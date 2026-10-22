"""Download pinned Windows runtime inputs; run inside schroot 2503."""
from pathlib import Path
import hashlib
import json
import subprocess

from common import ROOT, BUILD

hashes = json.loads((ROOT / "packaging/runtime-lock.json").read_text())
output = BUILD / "downloads"
output.mkdir(parents=True, exist_ok=True)
for name, expected in hashes.items():
    path = output / name
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        continue
    for base in (
        "https://www.python.org/ftp/python/3.13.12/amd64/",
        "https://registry.npmmirror.com/-/binary/python/3.13.12/amd64/",
    ):
        result = subprocess.run(
            [
                "curl",
                "-fsSL",
                "--connect-timeout",
                "15",
                "--max-time",
                "180",
                "-o",
                str(path),
                base + name,
            ]
        )
        if (
            result.returncode == 0
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        ):
            break
    else:
        path.unlink(missing_ok=True)
        raise SystemExit("Download failed or SHA-256 mismatch: " + name)
print("Verified runtime inputs")
