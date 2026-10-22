"""Keep a normal, minimizable OS window while removing its decorative frame."""
import ctypes as C
import ctypes.util
import os


def undecorate(root):
    root.update_idletasks()
    if os.name == "nt":
        from ctypes import wintypes as W

        user = C.WinDLL("user32", use_last_error=True)
        user.GetParent.argtypes = [W.HWND]
        user.GetParent.restype = W.HWND
        user.GetWindowLongW.argtypes = [W.HWND, C.c_int]
        user.GetWindowLongW.restype = W.LONG
        user.SetWindowLongW.argtypes = [W.HWND, C.c_int, W.LONG]
        user.SetWindowLongW.restype = W.LONG
        user.SetWindowPos.argtypes = [
            W.HWND,
            W.HWND,
            C.c_int,
            C.c_int,
            C.c_int,
            C.c_int,
            W.UINT,
        ]
        user.SetWindowPos.restype = W.BOOL
        hwnd = user.GetParent(root.winfo_id()) or root.winfo_id()
        style = user.GetWindowLongW(hwnd, -16)
        user.SetWindowLongW(hwnd, -16, (style & ~0x00C40000) | 0x000A0000)
        exstyle = user.GetWindowLongW(hwnd, -20)
        user.SetWindowLongW(hwnd, -20, (exstyle & ~0x80) | 0x40000)
        user.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0037)
        return
    # Tk on Linux uses X11 (or XWayland). Set Motif decoration hints on Tk's
    # wrapper, leaving override_redirect false so the WM can iconify it.
    x = C.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
    pointer = C.c_void_p
    window = C.c_ulong
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = pointer
    x.XQueryTree.argtypes = [
        pointer,
        window,
        C.POINTER(window),
        C.POINTER(window),
        C.POINTER(C.POINTER(window)),
        C.POINTER(C.c_uint),
    ]
    x.XQueryTree.restype = C.c_int
    x.XInternAtom.argtypes = [pointer, C.c_char_p, C.c_int]
    x.XInternAtom.restype = window
    x.XChangeProperty.argtypes = [
        pointer,
        window,
        window,
        window,
        C.c_int,
        C.c_int,
        pointer,
        C.c_int,
    ]
    x.XFree.argtypes = [pointer]
    x.XFlush.argtypes = [pointer]
    x.XCloseDisplay.argtypes = [pointer]
    display = x.XOpenDisplay(None)
    if not display:
        raise OSError("无法连接显示服务")
    try:
        parent, ancestor = window(), window()
        children = C.POINTER(window)()
        count = C.c_uint()
        if not x.XQueryTree(
            display,
            root.winfo_id(),
            C.byref(ancestor),
            C.byref(parent),
            C.byref(children),
            C.byref(count),
        ):
            raise OSError("无法获取窗口")
        if children:
            x.XFree(children)
        atom = x.XInternAtom(display, b"_MOTIF_WM_HINTS", False)
        hints = (C.c_ulong * 5)(2, 0, 0, 0, 0)
        x.XChangeProperty(
            display, parent.value, atom, atom, 32, 0, C.cast(hints, pointer), 5
        )
        x.XFlush(display)
    finally:
        x.XCloseDisplay(display)
