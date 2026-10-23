"""Desktop regression under Xvfb, with a real WM, tray host and compositor."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parent.parent
package_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "src"
sys.path.insert(0, str(package_path))
processes = []
app = None


def pump_until(predicate, timeout=8):
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        app.root.update()
        if predicate():
            return
        time.sleep(0.025)
    raise AssertionError("Desktop condition timed out")


def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)


def button(text):
    return next(
        w
        for w in widgets(app.dialog)
        if w.winfo_class() == "TButton" and w.cget("text") == text
    )


try:
    with tempfile.TemporaryDirectory(prefix="salary-desktop-") as temporary:
        os.environ["XDG_CONFIG_HOME"] = temporary
        os.environ["XDG_CONFIG_DIRS"] = str(Path(temporary) / "system")
        for args in (
            ["openbox"],
            [
                "stalonetray",
                "-c",
                "/dev/null",
                "--geometry",
                "2x1+0+0",
                "--icon-size",
                "24",
            ],
            ["xcompmgr", "-a"],
        ):
            processes.append(
                subprocess.Popen(
                    args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            )
        time.sleep(0.7)
        assert all(p.poll() is None for p in processes), "desktop services failed"
        from salary_motivator import app as m, model as payroll
        from salary_motivator.platform import autostart as startup

        # Existing users keep their salary and get sane defaults for new controls.
        old = dict(payroll.DEFAULTS, monthly="12345", overrides={})
        old.pop("opacity")
        old.pop("minimize_to_tray")
        payroll.CONFIG.parent.mkdir(parents=True)
        payroll.CONFIG.write_text(json.dumps(old))
        migrated = payroll.load_settings()
        assert migrated["monthly"] == "12345"
        assert migrated["opacity"] == 90 and migrated["minimize_to_tray"]
        app = m.SalaryWidget()
        pump_until(lambda: app.tray.ready)
        # The taskbar reads the WM's actual icon property, not the tray icon.
        properties = subprocess.check_output(
            ["xprop", "-name", app.root.title(), "_NET_WM_ICON", "WM_CLASS"],
            text=True,
        )
        assert "_NET_WM_ICON(CARDINAL)" in properties, properties
        assert '"Salarymotivator"' in properties, properties[-200:]
        assert not app.root.overrideredirect()
        assert abs(app.root.attributes("-alpha") - 0.9) < 0.01
        # Preview and cancel must restore the saved transparency.
        app.settings()
        app.root.update()
        scale = next(w for w in widgets(app.dialog) if w.winfo_class() == "TScale")
        scale.set(70)
        app.root.update()
        assert abs(app.root.attributes("-alpha") - 0.7) < 0.01
        button("取消").invoke()
        app.root.update()
        assert abs(app.root.attributes("-alpha") - 0.9) < 0.01
        # Save changes, then verify the value read back from disk.
        app.settings()
        app.root.update()
        scale = next(w for w in widgets(app.dialog) if w.winfo_class() == "TScale")
        scale.set(82)
        check = next(
            w
            for w in widgets(app.dialog)
            if w.winfo_class() == "TCheckbutton" and w.cget("text") == "最小化时收起到托盘"
        )
        check.invoke()
        button("保存").invoke()
        app.root.update()
        saved = payroll.load_settings()
        assert saved["opacity"] == 82 and not saved["minimize_to_tray"]
        for _ in range(3):
            app.minimize()
            pump_until(lambda: app.root.state() == "iconic")
            assert not app.root.winfo_ismapped()
            app.show()
            pump_until(
                lambda: app.root.state() == "normal" and app.root.winfo_ismapped()
            )
            assert abs(app.root.attributes("-alpha") - 0.82) < 0.01
        # Real XEmbed icon activation travels helper -> pipe -> Queue -> Tk.
        app.config["minimize_to_tray"] = True
        app.minimize()
        pump_until(lambda: app.hidden_to_tray and app.root.state() == "withdrawn")
        import ctypes as C

        x = C.CDLL("libX11.so.6")
        xt = C.CDLL("libXtst.so.6")
        x.XOpenDisplay.argtypes = [C.c_char_p]
        x.XOpenDisplay.restype = C.c_void_p
        x.XFlush.argtypes = [C.c_void_p]
        x.XCloseDisplay.argtypes = [C.c_void_p]
        xt.XTestFakeMotionEvent.argtypes = [
            C.c_void_p,
            C.c_int,
            C.c_int,
            C.c_int,
            C.c_ulong,
        ]
        xt.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        display = x.XOpenDisplay(None)
        try:
            xt.XTestFakeMotionEvent(display, -1, 12, 12, 0)
            xt.XTestFakeButtonEvent(display, 1, True, 0)
            xt.XTestFakeButtonEvent(display, 1, False, 0)
            x.XFlush(display)
        finally:
            x.XCloseDisplay(display)
        pump_until(lambda: not app.hidden_to_tray and app.root.winfo_ismapped())
        # Losing the tray host must restore the widget, preventing a lost window.
        app.hide_to_tray()
        pump_until(lambda: app.hidden_to_tray)
        processes[1].terminate()
        processes[1].wait(timeout=3)
        pump_until(
            lambda: not app.tray.ready
            and not app.hidden_to_tray
            and app.root.winfo_ismapped()
        )
        # Without a tray host, fall back to taskbar minimization.
        app.hide_to_tray()
        pump_until(lambda: app.root.state() == "iconic", timeout=7)
        app.show()
        app.root.update()
        app.events.put("settings")
        pump_until(lambda: app.dialog is not None and app.dialog.winfo_exists())
        app.events.put("quit")
        pump_until(lambda: app.closed)
        app = None
        print(
            "PASS: real taskbar minimize/restore x3, real tray click restore, tray-host loss recovery, no-host fallback, opacity preview/cancel/save, old-settings migration, tray settings/quit"
        )
finally:
    if app and not app.closed:
        app.quit()
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
