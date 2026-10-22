"""Run with the installed private Python; writes results to the supplied path."""
from pathlib import Path
import sys
import subprocess
import time

folder = Path(sys.argv[1])
report = Path(sys.argv[2])
sys.path.insert(0, str(folder / "app"))
from salary_motivator import app as m, model as payroll
from salary_motivator.platform import autostart as startup, single_instance

payroll.CONFIG.unlink(
    missing_ok=True
)  # test prefix only; reset previous smoke settings
assert startup.autostart_enabled(), "installer did not enable startup"
assert startup.startup_command() == [str(folder / "SalaryMotivator.exe")]
startup.set_autostart(False)
assert not startup.autostart_enabled()
startup.set_autostart(True)
assert startup.autostart_enabled()
assert m.acquire_instance()
assert not m.acquire_instance()
a = m.SalaryWidget()
a.root.update()


def pump_until(predicate, timeout=10):
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        a.root.update()
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError(
        "Windows desktop condition timed out; tray error: " + str(a.tray.error)
    )


pump_until(lambda: a.tray.ready)
assert not a.root.overrideredirect()
import ctypes as C
from ctypes import wintypes as W

user = C.WinDLL("user32")
user.GetParent.argtypes = [W.HWND]
user.GetParent.restype = W.HWND
user.GetWindowLongW.argtypes = [W.HWND, C.c_int]
user.GetWindowLongW.restype = W.LONG
user.ShowWindow.argtypes = [W.HWND, C.c_int]
user.IsIconic.argtypes = [W.HWND]
user.IsIconic.restype = W.BOOL
user.PostMessageW.argtypes = [W.HWND, W.UINT, C.c_size_t, C.c_ssize_t]
user.FindWindowW.argtypes = [W.LPCWSTR, W.LPCWSTR]
user.FindWindowW.restype = W.HWND
user.keybd_event.argtypes = [W.BYTE, W.BYTE, W.DWORD, C.c_size_t]
hwnd = user.GetParent(a.root.winfo_id())
assert not user.GetWindowLongW(hwnd, -16) & 0x00C00000, "caption reappeared"
assert user.GetWindowLongW(hwnd, -20) & 0x40000, "missing taskbar app window style"
a.config["minimize_to_tray"] = False
for _ in range(3):
    a.minimize()
    pump_until(lambda: a.root.state() == "iconic" and user.IsIconic(hwnd))
    user.ShowWindow(hwnd, 9)  # restore through OS, as the taskbar would
    pump_until(lambda: a.root.state() == "normal" and a.root.winfo_ismapped())
    assert not user.GetWindowLongW(hwnd, -16) & 0x00C00000
    assert abs(a.root.attributes("-alpha") - 0.9) < 0.01
a.config["minimize_to_tray"] = True
a.minimize()
pump_until(lambda: a.hidden_to_tray and a.root.state() == "withdrawn")
user.PostMessageW(a.tray.hwnd, 0x8001, 1, 0x0202)
pump_until(lambda: not a.hidden_to_tray and a.root.winfo_ismapped())
# Open the real native popup menu, select Settings through its accelerator.
a.hide_to_tray()
user.PostMessageW(a.tray.hwnd, 0x8001, 1, 0x0205)
pump_until(lambda: user.FindWindowW("#32768", None))
user.keybd_event(0x4F, 0, 0, 0)
user.keybd_event(0x4F, 0, 2, 0)
pump_until(lambda: a.dialog is not None and a.dialog.winfo_exists())
a.settings()
a.root.update()
assert a.dialog.winfo_exists()
# Launching the installed exe while a counter is open must exit successfully.
child = subprocess.run([str(folder / "SalaryMotivator.exe")], timeout=20)
assert child.returncode == 0, child.returncode


def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)


scale = next(w for w in widgets(a.dialog) if w.winfo_class() == "TScale")
scale.set(75)
a.root.update()
assert abs(a.root.attributes("-alpha") - 0.75) < 0.01
next(
    w
    for w in widgets(a.dialog)
    if w.winfo_class() == "TButton" and w.cget("text") == "取消"
).invoke()
assert abs(a.root.attributes("-alpha") - 0.9) < 0.01
a.settings()
a.root.update()
scale = next(w for w in widgets(a.dialog) if w.winfo_class() == "TScale")
scale.set(85)
next(
    w
    for w in widgets(a.dialog)
    if w.winfo_class() == "TButton" and w.cget("text") == "保存"
).invoke()
assert payroll.load_settings()["opacity"] == 85
# Quit from the real native tray menu and verify that its message loop ends.
user.PostMessageW(a.tray.hwnd, 0x8001, 1, 0x0205)
pump_until(lambda: user.FindWindowW("#32768", None))
user.keybd_event(0x51, 0, 0, 0)
user.keybd_event(0x51, 0, 2, 0)
pump_until(lambda: a.closed)
assert not a.tray.thread.is_alive()
# End the held instance lock, then run the real installed launch path.
single_instance.release_instance()
child = subprocess.Popen([str(folder / "SalaryMotivator.exe")])
time.sleep(3)
assert child.poll() is None, "installed launcher exited unexpectedly"
# Shut down only this test app's launcher tree.
subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], check=True)
report.write_text(
    "PASS: installed runtime imports Tk, GUI/settings, startup registry enable/disable, taskbar minimize/native restore x3, tray click, native tray settings/quit menu, opacity preview/cancel/save, duplicate launch, installed exe launch\n",
    encoding="utf-8",
)
