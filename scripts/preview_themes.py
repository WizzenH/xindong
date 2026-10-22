"""Capture actual Tk windows into a contact sheet, without changing user settings."""
import datetime as dt
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs/screenshots"
sys.path.insert(0, str(ROOT / "src"))


def capture(widget, filename):
    widget.update()
    image = Gdk.pixbuf_get_from_window(
        Gdk.get_default_root_window(),
        widget.winfo_rootx(),
        widget.winfo_rooty(),
        widget.winfo_width(),
        widget.winfo_height(),
    )
    if image is None:
        raise RuntimeError("Could not capture the rendered widget")
    image.savev(str(filename), "png", [], [])


with tempfile.TemporaryDirectory(prefix="salary-preview-") as temporary:
    os.environ["XDG_CONFIG_HOME"] = temporary
    os.environ["XDG_CONFIG_DIRS"] = temporary
    from salary_motivator.app import SalaryWidget
    from salary_motivator.themes import THEMES

    Gtk.init([])
    OUTPUT.mkdir(exist_ok=True)
    app = SalaryWidget()
    photos = []
    try:
        app.root.after_cancel(app._tick_after)
        app.apply_opacity(100)
        app.root.geometry("+0+0")
        demo_time = dt.datetime(2026, 10, 22, 13, 0)
        for key in THEMES:
            app.apply_theme(key)
            app.render_earnings(demo_time)
            filename = Path(temporary) / f"{key}.png"
            capture(app.root, filename)
            photos.append(tk.PhotoImage(file=str(filename)))

        app.config["theme"] = "rose_dusk"
        app.apply_theme("rose_dusk")
        app.settings()
        app.dialog.notebook.select(app.dialog.appearance)
        app.dialog.geometry("+0+0")
        capture(app.dialog, OUTPUT / "appearance.png")
        print("Settings preview:", app.dialog.winfo_width(), app.dialog.winfo_height())
        app.dialog.destroy()
        app.root.withdraw()

        gallery = tk.Toplevel(app.root)
        gallery.configure(bg="#EEF1F5")
        gallery.title("上班鼓励器 · 配色预览")
        gallery.geometry("+0+0")
        font = app.font
        tk.Label(
            gallery,
            text="给今天，换一种心情",
            font=(font, 21, "bold"),
            bg="#EEF1F5",
            fg="#202B3D",
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=22, pady=(20, 0))
        tk.Label(
            gallery,
            text="八套配色 · 同一金额示例 · 100% 不透明度对照 · v1.2.0",
            font=(font, 10),
            bg="#EEF1F5",
            fg="#5A677B",
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=22, pady=(6, 14))
        for index, (theme, photo) in enumerate(zip(THEMES.values(), photos)):
            card = tk.Frame(gallery, bg="#FFFFFF", padx=1, pady=1)
            card.grid(row=2 + index // 2, column=index % 2, padx=14, pady=(0, 16))
            tk.Label(
                card,
                text=theme.name,
                font=(font, 13, "bold"),
                bg="#FFFFFF",
                fg="#26344A",
                anchor="w",
            ).pack(fill="x", padx=12, pady=(10, 0))
            tk.Label(
                card,
                text=theme.description,
                font=(font, 9),
                bg="#FFFFFF",
                fg="#657187",
                anchor="w",
            ).pack(fill="x", padx=12, pady=(2, 10))
            tk.Label(card, image=photo, borderwidth=0).pack()
        capture(gallery, OUTPUT / "palettes.png")
        print("Contact sheet:", gallery.winfo_width(), gallery.winfo_height())
        gallery.destroy()
    finally:
        app.quit()
print("Actual UI screenshots saved.")
