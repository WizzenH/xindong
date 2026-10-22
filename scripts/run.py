#!/usr/bin/env python3
"""Run directly from a source checkout without installing the package."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from salary_motivator.app import main

main()
