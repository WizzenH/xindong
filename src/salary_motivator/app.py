#!/usr/bin/env python3
"""Salary Motivator: desktop widget entry point and window lifecycle."""
import datetime as dt
import os
import queue
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk

from .ui.preferences import PreferencesDialog
from .model import earnings, is_workday, load_settings, minutes
from .themes import THEMES
from .platform import tray, window_chrome
from .platform.single_instance import acquire_instance, release_instance


class SalaryWidget:
    def __init__(self):
        self.config = load_settings()
        self.theme = THEMES[self.config["theme"]]
        self.controls = []
        self.root = tk.Tk(className="SalaryMotivator")
        self.root.withdraw()
        self.root.title("上班鼓励器")
        self.window_icon = tk.PhotoImage(
            master=self.root,
            file=str(Path(__file__).parent / "assets/icon.png"),
        )
        self.root.iconphoto(
            True,
            self.window_icon,
            self.window_icon.subsample(4),
            self.window_icon.subsample(8),
        )
        self.root.geometry("420x286")
        self.root.resizable(False, False)
        self.root.configure(bg=self.theme.background)
        self.root.attributes("-topmost", True)
        self.dialog = None
        self.closed = False
        self.hidden_to_tray = False
        self.tray_pending = None
        self.events = queue.Queue()
        self.tray = tray.Tray(self.events)
        self.font = "Microsoft YaHei UI" if os.name == "nt" else "Noto Sans CJK SC"
        self.number_font = "Consolas" if os.name == "nt" else "DejaVu Sans Mono"
        self.setup_style()
        self.build_card()
        self.root.bind("<Escape>", lambda event: self.quit())
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.bind("<Map>", self.on_map, add="+")
        self.root.bind("<Destroy>", self.on_destroy, add="+")
        self.chrome = window_chrome
        self.refresh_chrome()
        self.apply_opacity(self.config["opacity"])
        self.root.deiconify()
        if os.name == "nt":
            icon = Path(__file__).parent / "assets/icon.ico"
            if icon.exists():
                self.root.iconbitmap(str(icon))
        self.tick()
        self.poll_tray()

    def build_card(self):
        canvas = self.canvas = tk.Canvas(
            self.root,
            width=420,
            height=286,
            bg=self.theme.background,
            highlightthickness=0,
        )
        canvas.pack()
        canvas.create_rectangle(
            0, 0, 419, 285, outline=self.theme.border, tags=("outline:border",)
        )
        canvas.create_oval(
            23, 24, 29, 30, fill=self.theme.accent, outline="", tags=("fill:accent",)
        )
        self.label(38, 27, "薪动 · PAYDAY", size=10, weight="bold")
        self.label(24, 69, "今日累计收入", color="muted")
        self.money_id = self.label(
            22, 113, "", size=34, color="money", weight="bold", numeric=True
        )
        self.rate_id = self.label(25, 151, "", color="positive")
        canvas.create_line(
            24, 180, 396, 180, fill=self.theme.border, tags=("fill:border",)
        )
        self.label(24, 201, "今日目标", size=9, color="muted")
        self.target_id = self.label(24, 223, "", size=12, numeric=True)
        self.label(247, 201, "本月工作日", size=9, color="muted")
        self.days_id = self.label(247, 223, "", size=12)
        canvas.create_line(
            26,
            250,
            394,
            250,
            fill=self.theme.track,
            width=4,
            capstyle="round",
            tags=("fill:track",),
        )
        self.progress_id = canvas.create_line(
            26,
            250,
            26,
            250,
            fill=self.theme.accent,
            width=4,
            capstyle="round",
            state="hidden",
            tags=("fill:accent",),
        )
        self.time_id = self.label(24, 269, "", size=8, color="muted")
        self.percent_id = canvas.create_text(
            396,
            269,
            text="",
            anchor="e",
            fill=self.theme.muted,
            font=(self.font, 8),
            tags=("fill:muted",),
        )
        self.control(280, "设置", self.settings, width=42)
        self.control(330, "−", self.minimize, width=22)
        self.control(360, "▾", self.hide_to_tray, width=22)
        self.control(390, "×", self.quit, width=22)
        canvas.bind("<ButtonPress-1>", self.drag_start)
        canvas.bind("<B1-Motion>", self.drag)

    def setup_style(self):
        theme = self.theme
        if not hasattr(self, "style"):
            self.style = ttk.Style(self.root)
            self.style.theme_use("clam")
        style = self.style
        style.configure(
            ".",
            background=theme.background,
            foreground=theme.foreground,
            font=(self.font, 10),
        )
        style.configure("TFrame", background=theme.background)
        style.configure(
            "TLabel", background=theme.background, foreground=theme.foreground
        )
        style.configure("Muted.TLabel", foreground=theme.muted)
        style.configure("Heading.TLabel", font=(self.font, 12, "bold"))
        style.configure("TNotebook", background=theme.background, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=theme.surface,
            foreground=theme.muted,
            padding=(16, 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme.accent)],
            foreground=[("selected", theme.accent_foreground)],
        )
        style.configure(
            "TEntry",
            fieldbackground=theme.surface,
            foreground=theme.foreground,
            insertcolor=theme.foreground,
            bordercolor=theme.border,
            padding=7,
            lightcolor=theme.border,
            darkcolor=theme.border,
        )
        style.configure(
            "TCombobox",
            fieldbackground=theme.surface,
            foreground=theme.foreground,
            arrowcolor=theme.foreground,
            background=theme.surface,
            bordercolor=theme.border,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme.surface)],
            foreground=[("readonly", theme.foreground)],
            selectbackground=[("readonly", theme.surface)],
            selectforeground=[("readonly", theme.foreground)],
        )
        style.configure(
            "TButton",
            background=theme.surface,
            foreground=theme.foreground,
            borderwidth=0,
            padding=(10, 7),
        )
        style.map("TButton", background=[("active", theme.hover)])
        style.configure(
            "Primary.TButton",
            background=theme.accent,
            foreground=theme.accent_foreground,
        )
        style.map("Primary.TButton", background=[("active", theme.accent)])
        style.configure(
            "TCheckbutton",
            background=theme.background,
            foreground=theme.foreground,
            indicatorbackground=theme.surface,
        )
        style.map(
            "TCheckbutton",
            background=[("active", theme.background)],
            indicatorbackground=[("selected", theme.accent)],
        )
        style.configure("TScale", background=theme.accent, troughcolor=theme.track)
        self.root.option_add("*TCombobox*Listbox.background", theme.surface)
        self.root.option_add("*TCombobox*Listbox.foreground", theme.foreground)

    def apply_theme(self, theme_key):
        self.theme = THEMES[theme_key]
        self.root.configure(bg=self.theme.background)
        self.canvas.configure(bg=self.theme.background)
        for role, color in self.theme.colors.items():
            self.canvas.itemconfigure(f"fill:{role}", fill=color)
            self.canvas.itemconfigure(f"outline:{role}", outline=color)
        for control in self.controls:
            control.configure(bg=self.theme.background, fg=self.theme.muted)
        self.setup_style()

    def label(
        self, x, y, text, size=10, color="foreground", weight="normal", numeric=False
    ):
        family = self.number_font if numeric else self.font
        return self.canvas.create_text(
            x,
            y,
            text=text,
            anchor="w",
            fill=getattr(self.theme, color),
            font=(family, size, weight),
            tags=(f"fill:{color}",),
        )

    def control(self, x, text, command, width):
        button = tk.Label(
            self.root,
            text=text,
            bg=self.theme.background,
            fg=self.theme.muted,
            font=(self.font, 10),
            cursor="hand2",
        )
        button.place(x=x, y=14, width=width, height=26)
        button.bind("<Button-1>", lambda event: command())
        button.bind(
            "<Enter>",
            lambda event: button.configure(bg=self.theme.hover, fg=self.theme.money),
        )
        button.bind(
            "<Leave>",
            lambda event: button.configure(
                bg=self.theme.background, fg=self.theme.muted
            ),
        )
        self.controls.append(button)

    def refresh_chrome(self):
        if not self.closed:
            try:
                self.chrome.undecorate(self.root)
            except (OSError, AttributeError, tk.TclError):
                pass

    def apply_opacity(self, value):
        try:
            self.root.attributes("-alpha", float(value) / 100)
            if hasattr(self, "_chrome_after"):
                self.root.after_cancel(self._chrome_after)
            self._chrome_after = self.root.after_idle(self.refresh_chrome)
        except tk.TclError:
            pass

    def on_map(self, event):
        if event.widget == self.root:
            self.apply_opacity(self.config["opacity"])

    def on_destroy(self, event):
        if event.widget == self.root and not self.closed:
            self.closed = True
            self.tray.stop()

    def quit(self):
        if self.closed:
            return
        self.closed = True
        if hasattr(self, "_chrome_after"):
            self.root.after_cancel(self._chrome_after)
        if hasattr(self, "_poll_after"):
            self.root.after_cancel(self._poll_after)
        if hasattr(self, "_tick_after"):
            self.root.after_cancel(self._tick_after)
        self.tray.stop()
        self.root.destroy()

    def minimize(self):
        if self.config["minimize_to_tray"]:
            self.hide_to_tray()
        else:
            self.minimize_taskbar()

    def minimize_taskbar(self):
        self.tray_pending = None
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.withdraw()
        self.hidden_to_tray = False
        self.root.iconify()

    def hide_to_tray(self):
        if self.tray.ready:
            self.tray_pending = None
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.withdraw()
            self.hidden_to_tray = True
            self.root.withdraw()
        else:
            # Never withdraw until an icon has actually registered with a host.
            self.tray_pending = time.monotonic() + 4

    def show(self):
        self.tray_pending = None
        self.hidden_to_tray = False
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.apply_opacity(self.config["opacity"])

    def poll_tray(self):
        if self.closed:
            return
        while True:
            try:
                command = self.events.get_nowait()
            except queue.Empty:
                break
            if command == "ready":
                self.tray.ready = True
            elif command == "unavailable":
                self.tray.ready = False
                if self.hidden_to_tray:
                    self.show()
            elif command == "show":
                self.show()
            elif command == "settings":
                self.show()
                self.settings()
            elif command == "quit":
                self.quit()
                return
        if self.tray_pending is not None:
            if self.tray.ready:
                self.hide_to_tray()
            elif time.monotonic() >= self.tray_pending:
                self.minimize_taskbar()
        self._poll_after = self.root.after(100, self.poll_tray)

    def drag_start(self, event):
        self.offset = (
            event.x_root - self.root.winfo_x(),
            event.y_root - self.root.winfo_y(),
        )

    def drag(self, event):
        if hasattr(self, "offset"):
            self.root.geometry(
                f"+{max(0, event.x_root-self.offset[0])}+{max(0, event.y_root-self.offset[1])}"
            )

    def tick(self):
        self.render_earnings(dt.datetime.now())
        self._tick_after = self.root.after(100, self.tick)

    def render_earnings(self, now):
        income = earnings(now, self.config)
        canvas = self.canvas
        amount_text = f"¥{income.amount:,.4f}"
        font_size = 34 if len(amount_text) <= 13 else 25
        canvas.itemconfigure(
            self.money_id,
            text=amount_text,
            font=(self.number_font, font_size, "bold"),
        )
        canvas.itemconfigure(self.target_id, text=f"¥{income.daily_target:,.2f}")
        canvas.itemconfigure(self.days_id, text=f"{income.working_days} 天")
        canvas.coords(self.progress_id, 26, 250, 26 + 368 * income.progress, 250)
        canvas.itemconfigure(
            self.progress_id, state="normal" if income.progress > 0 else "hidden"
        )
        canvas.itemconfigure(self.rate_id, text=self.income_status(now, income))
        canvas.itemconfigure(
            self.time_id,
            text=f"{now:%m.%d}  /  {self.config['start']} — {self.config['end']}",
        )
        canvas.itemconfigure(self.percent_id, text=f"{income.progress:.1%}")

    def income_status(self, now, income):
        if not is_workday(now.date(), self.config):
            return "今日休息 · 生活也值得投入"
        if income.progress >= 1:
            return "今日目标达成 · 下班快乐"
        if income.progress <= 0:
            return "尚未开工 · 美好的一天即将开始"
        working_seconds = (
            minutes(self.config["end"]) - minutes(self.config["start"])
        ) * 60
        rate = income.daily_target / working_seconds
        return f"↑  +¥{rate:.4f} / 秒   稳稳进账中"

    def settings(self):
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.reveal()
        else:
            self.dialog = PreferencesDialog(self)

    def run(self):
        self.root.mainloop()


def main():
    if not acquire_instance():
        return
    try:
        SalaryWidget().run()
    finally:
        release_instance()


if __name__ == "__main__":
    main()
