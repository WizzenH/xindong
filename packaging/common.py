"""Shared paths and the package's single version source for build scripts."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from salary_motivator import __version__ as VERSION

BUILD = Path(os.environ.get("SALARY_BUILD_DIR", ROOT / ".build-2503"))
DIST = Path(os.environ.get("SALARY_DIST_DIR", ROOT / "dist"))
PACKAGE = ROOT / "src/salary_motivator"
DIST.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
