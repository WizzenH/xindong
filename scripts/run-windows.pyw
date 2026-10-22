"""Source checkout entry point without a Windows console."""
from pathlib import Path
import runpy
import traceback

try:
    runpy.run_path(str(Path(__file__).with_name("run.py")), run_name="__main__")
except Exception:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, traceback.format_exc(), "上班鼓励器启动失败", 0x10)
