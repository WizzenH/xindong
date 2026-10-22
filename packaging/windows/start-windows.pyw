"""Entry point for the bundled, isolated Windows Python runtime."""
from pathlib import Path
import runpy
import sys
import traceback

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))
    runpy.run_module("salary_motivator", run_name="__main__")
except Exception:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, traceback.format_exc(), "上班鼓励器启动失败", 0x10)
    raise SystemExit(1)
