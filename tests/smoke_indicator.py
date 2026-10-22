"""Exercise the AppIndicator backend against a private StatusNotifier watcher."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time

if "--watcher" in sys.argv:
    import gi

    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    marker = Path(sys.argv[-1])
    node = Gio.DBusNodeInfo.new_for_xml(
        """<node><interface name="org.kde.StatusNotifierWatcher">
        <method name="RegisterStatusNotifierItem"><arg type="s" direction="in"/></method>
        <property name="IsStatusNotifierHostRegistered" type="b" access="read"/>
        <property name="ProtocolVersion" type="i" access="read"/>
        </interface></node>"""
    )

    def acquired(connection, name):
        def call(conn, sender, path, interface, method, args, invocation):
            marker.write_text(args.unpack()[0])
            invocation.return_value(None)

        def prop(conn, sender, path, interface, name):
            return (
                GLib.Variant("b", True)
                if name == "IsStatusNotifierHostRegistered"
                else GLib.Variant("i", 0)
            )

        connection.register_object(
            "/StatusNotifierWatcher", node.interfaces[0], call, prop, None
        )

    Gio.bus_own_name(
        Gio.BusType.SESSION,
        "org.kde.StatusNotifierWatcher",
        Gio.BusNameOwnerFlags.NONE,
        acquired,
        None,
        None,
    )
    GLib.MainLoop().run()
else:

    root = Path(__file__).resolve().parent.parent
    app = None
    wm = subprocess.Popen(
        ["openbox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    watcher = None
    try:
        with tempfile.TemporaryDirectory(prefix="salary-indicator-") as temporary:
            os.environ["XDG_CONFIG_HOME"] = temporary
            os.environ["XDG_CONFIG_DIRS"] = temporary
            marker = Path(temporary) / "registered"
            watcher = subprocess.Popen(
                [sys.executable, __file__, "--watcher", str(marker)]
            )
            time.sleep(0.6)
            sys.path.insert(0, str(root / "src"))
            from salary_motivator import app as m

            app = m.SalaryWidget()

            def until(predicate, timeout=8):
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    app.root.update()
                    if predicate():
                        return
                    time.sleep(0.03)
                raise AssertionError("AppIndicator condition timed out")

            until(lambda: marker.exists() and app.tray.ready)
            assert marker.read_text(), "missing StatusNotifier service registration"
            app.hide_to_tray()
            until(lambda: app.hidden_to_tray)
            watcher.terminate()
            watcher.wait(timeout=3)
            until(
                lambda: not app.tray.ready
                and not app.hidden_to_tray
                and app.root.winfo_ismapped()
            )
            print(
                "PASS: actual Ayatana AppIndicator registration with KDE watcher, tray-host loss restores window"
            )
    finally:
        if app:
            app.quit()
        for process in (watcher, wm):
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
