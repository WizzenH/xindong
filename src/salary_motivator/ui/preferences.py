"""Settings dialog: calendar editing and appearance preview with explicit save/cancel."""
import calendar
import datetime as dt
from decimal import InvalidOperation
import tkinter as tk
from tkinter import messagebox, ttk

from .appearance import AppearancePanel
from .. import model as payroll
from ..platform import autostart as startup


WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


class PreferencesDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("工资与工作日设置")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda event: self.cancel())

        today = dt.date.today()
        self.year = today.year
        self.month = today.month
        self.overrides = dict(app.config["overrides"])
        self.form = {
            key: tk.StringVar(value=str(app.config[key]))
            for key in ("monthly", "rest", "start", "end")
        }
        self.single_rest = tk.StringVar(value=WEEKDAYS[app.config["single_rest"]])
        self.calendar_title = tk.StringVar()
        self.calendar_summary = tk.StringVar()

        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)
        self.calendar_page = ttk.Frame(self.notebook, padding=(8, 12))
        self.notebook.add(self.calendar_page, text="工资与日历")
        self.build_calendar_page()

        self.appearance = AppearancePanel(
            self.notebook,
            app.config,
            startup_enabled=startup.autostart_enabled(),
            on_theme_change=self.preview_theme,
            on_opacity_change=app.apply_opacity,
        )
        self.notebook.add(self.appearance, text="外观与启动")
        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="保存", style="Primary.TButton", command=self.save).pack(
            side="right"
        )
        ttk.Button(actions, text="取消", command=self.cancel).pack(side="right", padx=8)

        self.form["rest"].trace_add("write", self.render_calendar)
        self.single_rest.trace_add("write", self.render_calendar)
        self.render_calendar()

    def build_calendar_page(self):
        fields = (
            ("monthly", "月薪（元）"),
            ("rest", "休息方式"),
            ("start", "上班时间 HH:MM"),
            ("end", "下班时间 HH:MM"),
        )
        for row, (key, label) in enumerate(fields):
            ttk.Label(self.calendar_page, text=label).grid(
                row=row, column=0, sticky="w", pady=4, padx=(0, 12)
            )
            if key == "rest":
                widget = ttk.Combobox(
                    self.calendar_page,
                    textvariable=self.form[key],
                    values=("单休", "双休"),
                    state="readonly",
                    width=20,
                )
            else:
                widget = ttk.Entry(
                    self.calendar_page, textvariable=self.form[key], width=23
                )
            widget.grid(row=row, column=1, sticky="ew")
        ttk.Label(self.calendar_page, text="单休的休息日").grid(
            row=4, column=0, sticky="w", pady=4
        )
        ttk.Combobox(
            self.calendar_page,
            textvariable=self.single_rest,
            values=WEEKDAYS,
            state="readonly",
            width=20,
        ).grid(row=4, column=1, sticky="ew")

        navigation = ttk.Frame(self.calendar_page)
        navigation.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Button(
            navigation, text="‹", width=3, command=lambda: self.move_month(-1)
        ).pack(side="left")
        ttk.Label(navigation, textvariable=self.calendar_title).pack(
            side="left", expand=True
        )
        ttk.Button(
            navigation, text="›", width=3, command=lambda: self.move_month(1)
        ).pack(side="right")
        self.calendar_grid = ttk.Frame(self.calendar_page)
        self.calendar_grid.grid(row=6, column=0, columnspan=2)
        ttk.Label(self.calendar_page, textvariable=self.calendar_summary).grid(
            row=7, column=0, columnspan=2, pady=(8, 2)
        )
        ttk.Label(
            self.calendar_page,
            text="点击日期切换班/休，* 表示手动调整。\n" "法定节假日、调休请手动标记。\n" "日薪 = 月薪 ÷ 当月工作日，班内连续线性增长。",
            style="Muted.TLabel",
        ).grid(row=8, column=0, columnspan=2, pady=6)
        ttk.Button(self.calendar_page, text="重置本月调休", command=self.reset_month).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    def calendar_settings(self):
        return dict(
            self.app.config,
            **{key: value.get() for key, value in self.form.items()},
            single_rest=WEEKDAYS.index(self.single_rest.get()),
            overrides=self.overrides,
        )

    def render_calendar(self, *_):
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()
        settings = self.calendar_settings()
        theme = self.app.theme
        self.calendar_title.set(f"{self.year} 年 {self.month} 月")
        for column, name in enumerate("一二三四五六日"):
            ttk.Label(self.calendar_grid, text=name, anchor="center").grid(
                row=0, column=column
            )
        for row, week in enumerate(calendar.monthcalendar(self.year, self.month), 1):
            for column, number in enumerate(week):
                if not number:
                    continue
                day = dt.date(self.year, self.month, number)
                working = payroll.is_workday(day, settings)
                manually_set = day.isoformat() in self.overrides
                caption = (
                    f"{number}{'班' if working else '休'}{'*' if manually_set else ''}"
                )
                tk.Button(
                    self.calendar_grid,
                    text=caption,
                    width=5,
                    bg=theme.work_background if working else theme.surface,
                    fg=theme.work_foreground if working else theme.muted,
                    activebackground=theme.work_hover if working else theme.hover,
                    activeforeground=theme.work_foreground
                    if working
                    else theme.foreground,
                    relief="flat",
                    borderwidth=0,
                    pady=6,
                    cursor="hand2",
                    command=lambda chosen_day=day: self.toggle_workday(chosen_day),
                ).grid(row=row, column=column, padx=1, pady=1)
        count = payroll.workdays(self.year, self.month, settings)
        self.calendar_summary.set(f"本月计薪工作日：{count} 天")

    def toggle_workday(self, day):
        settings = self.calendar_settings()
        new_value = not payroll.is_workday(day, settings)
        default_value = payroll.is_workday(day, dict(settings, overrides={}))
        if new_value == default_value:
            self.overrides.pop(day.isoformat(), None)
        else:
            self.overrides[day.isoformat()] = new_value
        self.render_calendar()

    def move_month(self, delta):
        index = self.year * 12 + self.month - 1 + delta
        year, month = divmod(index, 12)
        if 1 <= year <= 9999:
            self.year, self.month = year, month + 1
            self.render_calendar()

    def reset_month(self):
        prefix = f"{self.year:04d}-{self.month:02d}-"
        self.overrides = {
            day: working
            for day, working in self.overrides.items()
            if not day.startswith(prefix)
        }
        self.render_calendar()

    def preview_theme(self, theme_key):
        self.app.apply_theme(theme_key)
        self.render_calendar()

    def reveal(self):
        self.deiconify()
        self.lift()
        self.preview_theme(self.appearance.theme_key.get())
        self.app.apply_opacity(self.appearance.opacity.get())

    def cancel(self):
        self.app.apply_theme(self.app.config["theme"])
        self.app.apply_opacity(self.app.config["opacity"])
        self.destroy()

    def save(self):
        settings = dict(self.calendar_settings(), **self.appearance.settings_values())
        try:
            payroll.validate(settings)
            desired_startup = self.appearance.autostart.get()
            if desired_startup != startup.autostart_enabled():
                startup.set_autostart(desired_startup)
            payroll.save_settings(settings)
        except (ValueError, InvalidOperation, OSError) as error:
            messagebox.showerror("无法保存", str(error), parent=self)
            return
        self.app.config = settings
        self.app.apply_theme(settings["theme"])
        self.app.apply_opacity(settings["opacity"])
        self.destroy()
