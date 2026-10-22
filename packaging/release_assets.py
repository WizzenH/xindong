"""Create a tracked-source archive and checksums for this version only."""
import hashlib
import subprocess

from common import DIST, ROOT, VERSION

source_archive = DIST / f"xindong-{VERSION}-source.zip"
subprocess.run(
    [
        "git",
        "archive",
        "--format=zip",
        f"--prefix=xindong-{VERSION}/",
        "HEAD",
        "-o",
        str(source_archive),
    ],
    cwd=ROOT,
    check=True,
)
files = [
    DIST / f"SalaryMotivator-{VERSION}-win64-setup.exe",
    DIST / f"salary-motivator_{VERSION}_all.deb",
    source_archive,
]
for file in files:
    if not file.is_file():
        raise SystemExit("Missing release asset: " + file.name)
checksums = "".join(
    f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}\n" for file in files
)
(DIST / "SHA256SUMS").write_text(checksums, encoding="utf-8")
print(checksums)
