"""Appearance controls and palette previews, separate from payroll/calendar UI."""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict

from ..themes import THEMES


class AppearancePanel(ttk.Frame):
    def __init__(
        self,
        parent,
        settings: Dict,
        startup_enabled: bool,
        on_theme_change: Callable[[str], None],
        on_opacity_change: Callable[[float], None],
    ):
        super().__init__(parent, padding=(8, 12))
        self.theme_key = tk.StringVar(value=settings["theme"])
        self.opacity = tk.DoubleVar(value=settings["opacity"])
        self.autostart = tk.BooleanVar(value=startup_enabled)
        self.minimize_to_tray = tk.BooleanVar(value=settings["minimize_to_tray"])
        self.on_theme_change = on_theme_change
        self.on_opacity_change = on_opacity_change
        self.cards = {}
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="选一种今天的心情色", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        palette_grid = ttk.Frame(self)
        palette_grid.grid(row=1, column=0, columnspan=2, sticky="ew")
        for index, theme in enumerate(THEMES.values()):
            self.create_theme_card(palette_grid, index, theme)

        self.theme_description = tk.StringVar()
        ttk.Label(self, textvariable=self.theme_description, style="Muted.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 18)
        )
        self.opacity_description = tk.StringVar()
        ttk.Label(self, textvariable=self.opacity_description).grid(
            row=3, column=0, sticky="w", padx=(0, 12)
        )
        ttk.Scale(self, from_=65, to=100, variable=self.opacity).grid(
            row=3, column=1, sticky="ew"
        )
        ttk.Checkbutton(self, text="登录电脑后自动启动", variable=self.autostart).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(20, 8)
        )
        ttk.Checkbutton(self, text="最小化时收起到托盘", variable=self.minimize_to_tray).grid(
            row=5, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            self,
            text="切换配色和透明度可实时预览；点击保存后记住选择。",
            style="Muted.TLabel",
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(16, 0))

        self.theme_key.trace_add("write", self.preview_theme)
        self.opacity.trace_add("write", self.preview_opacity)
        self.refresh_selection()
        self.update_opacity_description()

    def create_theme_card(self, parent, index, theme):
        card = tk.Frame(
            parent,
            bg=theme.background,
            highlightthickness=2,
            highlightbackground=theme.border,
            padx=10,
            pady=10,
            cursor="hand2",
        )
        card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=4)
        parent.columnconfigure(index % 2, weight=1)
        choose = lambda: self.theme_key.set(theme.key)
        title = tk.Button(
            card,
            text=theme.name,
            bg=theme.background,
            fg=theme.foreground,
            activebackground=theme.surface,
            activeforeground=theme.foreground,
            relief="flat",
            borderwidth=0,
            anchor="w",
            cursor="hand2",
            command=choose,
        )
        title.pack(fill="x")
        swatches = tk.Frame(card, bg=theme.background)
        swatches.pack(fill="x", pady=(8, 0))
        for color in (theme.surface, theme.money, theme.accent, theme.positive):
            swatch = tk.Frame(swatches, bg=color, width=40, height=6, cursor="hand2")
            swatch.pack(side="left", fill="x", expand=True, padx=(0, 3))
            swatch.bind(
                "<Button-1>", lambda event, key=theme.key: self.theme_key.set(key)
            )
        card.bind("<Button-1>", lambda event: choose())
        self.cards[theme.key] = (card, title)

    def refresh_selection(self):
        selected = self.theme_key.get()
        self.theme_description.set(THEMES[selected].description)
        for key, (card, title) in self.cards.items():
            theme = THEMES[key]
            card.configure(
                highlightbackground=theme.accent if key == selected else theme.border
            )
            title.configure(text=("✓  " if key == selected else "") + theme.name)

    def preview_theme(self, *_):
        self.refresh_selection()
        self.on_theme_change(self.theme_key.get())

    def update_opacity_description(self):
        self.opacity_description.set(f"窗口不透明度：{self.opacity.get():.0f}%")

    def preview_opacity(self, *_):
        self.update_opacity_description()
        self.on_opacity_change(self.opacity.get())

    def settings_values(self) -> Dict:
        return {
            "theme": self.theme_key.get(),
            "opacity": int(round(self.opacity.get())),
            "minimize_to_tray": self.minimize_to_tray.get(),
        }
