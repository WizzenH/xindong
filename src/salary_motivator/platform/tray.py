"""Native Windows notification icon; isolated GTK helper on Linux.

Only plain commands cross into the Tk thread through a Queue. No Tk calls
are made by tray callbacks or helper reader threads.
"""
import os
from pathlib import Path
import subprocess
import sys
import threading


class Tray:
    def __init__(self, events):
        self.events = events
        self.ready = False
        self.closed = False
        self.error = None
        self.process = None
        self.hwnd = None
        self.thread = threading.Thread(
            target=self._windows if os.name == "nt" else self._linux, daemon=True
        )
        self.thread.start()

    def emit(self, command):
        if not self.closed:
            self.events.put(command)

    def stop(self):
        self.closed = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        if self.hwnd:
            import ctypes
            from ctypes import wintypes

            user = ctypes.WinDLL("user32")
            user.PostMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                ctypes.c_size_t,
                ctypes.c_ssize_t,
            ]
            user.PostMessageW(self.hwnd, 0x0010, 0, 0)
        if self.thread is not threading.current_thread():
            self.thread.join(timeout=2)

    def _linux(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--helper"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if self.closed:
                self.process.terminate()
            for line in self.process.stdout:
                command = line.strip()
                if command in ("ready", "unavailable", "show", "settings", "quit"):
                    self.emit(command)
        except OSError:
            pass
        finally:
            self.emit("unavailable")

    def _windows(self):
        import ctypes as C
        from ctypes import wintypes as W

        try:
            user = C.WinDLL("user32", use_last_error=True)
            shell = C.WinDLL("shell32", use_last_error=True)
            kernel = C.WinDLL("kernel32", use_last_error=True)
            callback_type = C.WINFUNCTYPE(
                C.c_ssize_t, W.HWND, W.UINT, C.c_size_t, C.c_ssize_t
            )

            class WindowClass(C.Structure):
                _fields_ = [
                    ("style", W.UINT),
                    ("proc", callback_type),
                    ("cls_extra", C.c_int),
                    ("wnd_extra", C.c_int),
                    ("instance", W.HINSTANCE),
                    ("icon", W.HICON),
                    ("cursor", W.HANDLE),
                    ("background", W.HBRUSH),
                    ("menu", W.LPCWSTR),
                    ("name", W.LPCWSTR),
                ]

            class NotifyData(C.Structure):
                _fields_ = [
                    ("size", W.DWORD),
                    ("hwnd", W.HWND),
                    ("id", W.UINT),
                    ("flags", W.UINT),
                    ("message", W.UINT),
                    ("icon", W.HICON),
                    ("tip", W.WCHAR * 128),
                    ("state", W.DWORD),
                    ("mask", W.DWORD),
                    ("info", W.WCHAR * 256),
                    ("version", W.UINT),
                    ("title", W.WCHAR * 64),
                    ("info_flags", W.DWORD),
                    ("guid", C.c_byte * 16),
                    ("balloon", W.HICON),
                ]

            kernel.GetModuleHandleW.argtypes = [W.LPCWSTR]
            kernel.GetModuleHandleW.restype = W.HMODULE
            user.RegisterClassW.argtypes = [C.POINTER(WindowClass)]
            user.RegisterClassW.restype = W.ATOM
            user.UnregisterClassW.argtypes = [W.LPCWSTR, W.HINSTANCE]
            user.CreateWindowExW.argtypes = [
                W.DWORD,
                W.LPCWSTR,
                W.LPCWSTR,
                W.DWORD,
                C.c_int,
                C.c_int,
                C.c_int,
                C.c_int,
                W.HWND,
                W.HMENU,
                W.HINSTANCE,
                C.c_void_p,
            ]
            user.CreateWindowExW.restype = W.HWND
            user.DefWindowProcW.argtypes = [W.HWND, W.UINT, C.c_size_t, C.c_ssize_t]
            user.DefWindowProcW.restype = C.c_ssize_t
            user.LoadImageW.argtypes = [
                W.HINSTANCE,
                W.LPCWSTR,
                W.UINT,
                C.c_int,
                C.c_int,
                W.UINT,
            ]
            user.LoadImageW.restype = W.HANDLE
            user.LoadIconW.argtypes = [W.HINSTANCE, C.c_void_p]
            user.LoadIconW.restype = W.HICON
            user.DestroyIcon.argtypes = [W.HICON]
            user.CreatePopupMenu.restype = W.HMENU
            user.AppendMenuW.argtypes = [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR]
            user.SetForegroundWindow.argtypes = [W.HWND]
            user.TrackPopupMenu.argtypes = [
                W.HMENU,
                W.UINT,
                C.c_int,
                C.c_int,
                C.c_int,
                W.HWND,
                C.c_void_p,
            ]
            user.TrackPopupMenu.restype = W.UINT
            user.GetCursorPos.argtypes = [C.POINTER(W.POINT)]
            user.DestroyMenu.argtypes = [W.HMENU]
            user.PostMessageW.argtypes = [W.HWND, W.UINT, C.c_size_t, C.c_ssize_t]
            user.DestroyWindow.argtypes = [W.HWND]
            user.PostQuitMessage.argtypes = [C.c_int]
            user.RegisterWindowMessageW.argtypes = [W.LPCWSTR]
            user.RegisterWindowMessageW.restype = W.UINT
            user.GetMessageW.argtypes = [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT]
            user.GetMessageW.restype = C.c_int
            user.TranslateMessage.argtypes = [C.POINTER(W.MSG)]
            user.DispatchMessageW.argtypes = [C.POINTER(W.MSG)]
            user.DispatchMessageW.restype = C.c_ssize_t
            shell.Shell_NotifyIconW.argtypes = [W.DWORD, C.POINTER(NotifyData)]
            shell.Shell_NotifyIconW.restype = W.BOOL
            notify = NotifyData()
            own_icon = None
            taskbar_created = user.RegisterWindowMessageW("TaskbarCreated")

            def register():
                success = bool(shell.Shell_NotifyIconW(0, C.byref(notify)))
                self.emit("ready" if success else "unavailable")

            @callback_type
            def callback(hwnd, message, wparam, lparam):
                if message == taskbar_created:
                    register()
                    return 0
                if message == 0x8001:
                    if lparam in (0x0202, 0x0203):  # click / double click
                        self.emit("show")
                    elif lparam in (0x0205, 0x007B):
                        menu = user.CreatePopupMenu()
                        for ident, text in (
                            (1, "显示窗口(&S)"),
                            (2, "设置(&O)"),
                            (3, "退出(&Q)"),
                        ):
                            user.AppendMenuW(menu, 0, ident, text)
                        point = W.POINT()
                        user.GetCursorPos(C.byref(point))
                        user.SetForegroundWindow(hwnd)
                        selected = user.TrackPopupMenu(
                            menu, 0x0102, point.x, point.y, 0, hwnd, None
                        )
                        user.DestroyMenu(menu)
                        user.PostMessageW(hwnd, 0, 0, 0)
                        if selected:
                            self.emit({1: "show", 2: "settings", 3: "quit"}[selected])
                    return 0
                if message == 0x0010:
                    user.DestroyWindow(hwnd)
                    return 0
                if message == 0x0002:
                    user.PostQuitMessage(0)
                    return 0
                return user.DefWindowProcW(hwnd, message, wparam, lparam)

            instance = kernel.GetModuleHandleW(None)
            name = "SalaryMotivatorTray_" + str(os.getpid())
            wc = WindowClass()
            wc.proc, wc.instance, wc.name = callback, instance, name
            if not user.RegisterClassW(C.byref(wc)):
                raise C.WinError(C.get_last_error())
            try:
                self.hwnd = user.CreateWindowExW(
                    0,
                    name,
                    "Salary Motivator",
                    0,
                    0,
                    0,
                    0,
                    0,
                    None,
                    None,
                    instance,
                    None,
                )
                if not self.hwnd:
                    raise C.WinError(C.get_last_error())
                path = Path(__file__).resolve().parents[1] / "assets/icon.ico"
                own_icon = (
                    user.LoadImageW(None, str(path), 1, 32, 32, 0x10)
                    if path.exists()
                    else None
                )
                notify.size, notify.hwnd, notify.id = C.sizeof(notify), self.hwnd, 1
                notify.flags, notify.message = 7, 0x8001
                notify.icon = own_icon or user.LoadIconW(None, C.c_void_p(32512))
                notify.tip = "薪动 · 上班鼓励器 — 点击显示，右键菜单"
                register()
                if self.closed:
                    user.DestroyWindow(self.hwnd)
                else:
                    msg = W.MSG()
                    while user.GetMessageW(C.byref(msg), None, 0, 0) > 0:
                        user.TranslateMessage(C.byref(msg))
                        user.DispatchMessageW(C.byref(msg))
            finally:
                if notify.hwnd:
                    shell.Shell_NotifyIconW(2, C.byref(notify))
                if own_icon:
                    user.DestroyIcon(own_icon)
                self.hwnd = None
                user.UnregisterClassW(name, instance)
        except Exception as error:
            self.error = repr(error)
            self.emit("unavailable")
        finally:
            self.emit("unavailable")


def linux_helper():
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gio

    if not Gtk.init_check()[0]:
        return
    icon = Path(__file__).resolve().parents[1] / "assets/icon.svg"

    def send(command):
        print(command, flush=True)

    menu = Gtk.Menu()
    for command, label in (("show", "显示窗口"), ("settings", "设置"), ("quit", "退出")):
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda widget, action=command: send(action))
        menu.append(item)
    menu.show_all()

    def watcher_available():
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            return False
        for name in (
            "org.kde.StatusNotifierWatcher",
            "org.freedesktop.StatusNotifierWatcher",
        ):
            try:
                reply = bus.call_sync(
                    name,
                    "/StatusNotifierWatcher",
                    "org.freedesktop.DBus.Properties",
                    "Get",
                    GLib.Variant("(ss)", (name, "IsStatusNotifierHostRegistered")),
                    None,
                    Gio.DBusCallFlags.NONE,
                    500,
                    None,
                )
                if reply.get_child_value(0).get_variant().get_boolean():
                    return True
            except GLib.Error:
                continue
        return False

    indicator = None
    if watcher_available():
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as Indicator
        except (ValueError, ImportError):
            try:
                gi.require_version("AppIndicator3", "0.1")
                from gi.repository import AppIndicator3 as Indicator
            except (ValueError, ImportError):
                Indicator = None
        if Indicator:
            indicator = Indicator.Indicator.new(
                "salary-motivator",
                str(icon),
                Indicator.IndicatorCategory.APPLICATION_STATUS,
            )
            indicator.set_menu(menu)
            indicator.set_status(Indicator.IndicatorStatus.ACTIVE)
    status = None
    if indicator is None:
        status = Gtk.StatusIcon.new_from_file(str(icon))
        status.set_title("上班鼓励器")
        status.set_tooltip_text("薪动 · 点击显示，右键打开菜单")
        status.connect("activate", lambda widget: send("show"))
        status.connect(
            "popup-menu",
            lambda widget, button, when: menu.popup(
                None, None, Gtk.StatusIcon.position_menu, widget, button, when
            ),
        )
        status.set_visible(True)
    last = [None]

    def health():
        available = (
            (watcher_available() and indicator.get_property("connected"))
            if indicator
            else status.is_embedded()
        )
        if available != last[0]:
            send("ready" if available else "unavailable")
            last[0] = available
        return True

    GLib.timeout_add(500, health)
    # Do not leave a helper alive if the Tk process exits unexpectedly.
    parent_pid = os.getppid()

    def parent_alive():
        if os.getppid() != parent_pid:
            Gtk.main_quit()
            return False
        return True

    GLib.timeout_add_seconds(2, parent_alive)
    Gtk.main()


if __name__ == "__main__" and "--helper" in sys.argv:
    linux_helper()
