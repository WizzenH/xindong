#!/usr/bin/env python3
"""Build in schroot 2503. Runtime MSI inputs live in .build-2503/downloads."""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import subprocess

from common import BUILD as build, DIST, PACKAGE, ROOT as root, VERSION

app = build / "windows-app"
if app.exists():
    shutil.rmtree(app)
runtime = app / "runtime"
runtime.mkdir(parents=True)
manifest = json.loads((root / "packaging/runtime-lock.json").read_text())
for name, expected in manifest.items():
    source = build / "downloads" / name
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit("Runtime input SHA-256 mismatch: " + name)
    subprocess.run(
        ["msiextract", "-C", str(runtime), str(source)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
shutil.copytree(
    PACKAGE,
    app / "app/salary_motivator",
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
for name in ("README.md", "LICENSE"):
    shutil.copy2(root / name, app / name)
shutil.copy2(root / "packaging/windows/start-windows.pyw", app / "start-windows.pyw")
# A small original currency icon in standard 32-bit ICO format.
size = 64
pixels = bytearray()
for y in reversed(range(size)):
    for x in range(size):
        ink = (
            (
                14 <= y <= 31
                and (
                    abs(x - (18 + (y - 14) * 0.82)) < 2.5
                    or abs(x - (46 - (y - 14) * 0.82)) < 2.5
                )
            )
            or (30 <= y <= 51 and abs(x - 32) <= 2)
            or (21 <= x <= 43 and (abs(y - 34) <= 2 or abs(y - 42) <= 2))
        )
        r, g, b = (213, 249, 168) if ink else (23, 28, 38)
        pixels.extend((b, g, r, 255))
bitmap = (
    struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    + pixels
    + bytes(size * size // 8)
)
(build / "app.ico").write_bytes(
    struct.pack("<HHH", 0, 1, 1)
    + struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(bitmap), 22)
    + bitmap
)
shutil.copy2(build / "app.ico", app / "app/salary_motivator/assets/icon.ico")
(build / "launcher.rc").write_text('1 ICON "app.ico"\n')
subprocess.run(
    ["x86_64-w64-mingw32-windres", "launcher.rc", "-O", "coff", "-o", "launcher-res.o"],
    cwd=build,
    check=True,
)
subprocess.run(
    [
        "x86_64-w64-mingw32-gcc",
        "-Os",
        "-s",
        "-municode",
        "-mwindows",
        str(root / "packaging/windows/launcher.c"),
        str(build / "launcher-res.o"),
        "-o",
        str(app / "SalaryMotivator.exe"),
    ],
    check=True,
)
subprocess.run(
    [
        "makensis",
        "-V2",
        f"-DAPP_VERSION={VERSION}",
        f"-DPAYLOAD_DIR={app}",
        f"-DAPP_ICON={build / 'app.ico'}",
        f"-DOUTPUT_FILE={DIST / ('SalaryMotivator-' + VERSION + '-win64-setup.exe')}",
        "installer.nsi",
    ],
    cwd=root / "packaging/windows",
    check=True,
)
print("Windows installer ready:", VERSION)
