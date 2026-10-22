"""Validate an installed Windows package in a disposable Wine prefix."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from salary_motivator import __version__

parser = argparse.ArgumentParser()
parser.add_argument("--wine", default=shutil.which("wine"))
parser.add_argument("--wineserver")
parser.add_argument(
    "--library-path", help="Optional loader libraries for a packaged Wine runtime"
)
args = parser.parse_args()
if not args.wine:
    parser.error("Supply --wine /path/to/wine")
wine = str(Path(args.wine).resolve())
wineserver = args.wineserver or str(Path(wine).with_name("wineserver"))
build = ROOT / ".build-2503"
prefix = build / "test-prefix"
build.mkdir(exist_ok=True)
env = dict(os.environ, WINEPREFIX=str(prefix), WINEDEBUG="-all", WINEARCH="win64")
if args.library_path:
    env["LD_LIBRARY_PATH"] = args.library_path


def run(*arguments, timeout=90):
    subprocess.run([wine, *map(str, arguments)], env=env, check=True, timeout=timeout)


def windows_path(path):
    return "Z:" + str(path.resolve()).replace("/", "\\")


run(ROOT / f"dist/SalaryMotivator-{__version__}-win64-setup.exe", "/S")
probe = build / "probe-install.cmd"
location = build / "installed-location.txt"
probe.write_text(
    '@echo off\necho %LOCALAPPDATA%\\Programs\\SalaryMotivator>"'
    + windows_path(location)
    + '"\n'
)
run("cmd", "/c", windows_path(probe))
folder = location.read_text().strip()
report = ROOT / "dist/windows-smoke.txt"
run(
    folder + r"\runtime\python.exe",
    "-I",
    windows_path(ROOT / "tests/smoke_windows.py"),
    folder,
    windows_path(report),
)
run(folder + r"\Uninstall.exe", "/S")
subprocess.run([wineserver, "-w"], env=env, timeout=30, check=True)
result = subprocess.run(
    [
        wine,
        "reg",
        "query",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "/v",
        "SalaryMotivator",
    ],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
assert result.returncode != 0, "startup entry survived uninstall"
installed = prefix / "drive_c" / folder[3:].replace("\\", "/")
for owned in (
    "runtime",
    "app/salary_motivator",
    "SalaryMotivator.exe",
    "start-windows.pyw",
):
    assert not (installed / owned).exists(), (
        "application file survived uninstall: " + owned
    )
with report.open("a") as handle:
    handle.write(
        "PASS: silent installer/uninstaller and startup registration cleanup (Wine)\n"
    )
print(report.read_text())
