"""Payroll calculations and settings persistence; no desktop toolkit dependency."""
import calendar
import datetime as dt
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import NamedTuple

from .themes import DEFAULT_THEME, THEMES

CONFIG_HOME = (
    Path(os.environ.get("APPDATA", Path.home()))
    if os.name == "nt"
    else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
)
CONFIG = CONFIG_HOME / "salary-motivator" / "settings.json"
AUTOSTART_NAME = "salary-motivator.desktop"
DEFAULTS = dict(
    monthly="10000",
    rest="双休",
    single_rest=6,
    start="08:30",
    end="17:30",
    overrides={},
    opacity=90,
    minimize_to_tray=True,
    theme=DEFAULT_THEME,
)


def save_settings(settings):
    validate(settings)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(CONFIG)


def minutes(value):
    parsed_time = dt.datetime.strptime(value, "%H:%M")
    return parsed_time.hour * 60 + parsed_time.minute


def is_workday(day, settings):
    override = settings["overrides"].get(day.isoformat())
    if override is not None:
        return override
    if settings["rest"] == "双休":
        return day.weekday() < 5
    return day.weekday() != settings["single_rest"]


def workdays(year, month, settings):
    return sum(
        is_workday(dt.date(year, month, n), settings)
        for n in range(1, calendar.monthrange(year, month)[1] + 1)
    )


class Earnings(NamedTuple):
    amount: Decimal
    daily_target: Decimal
    working_days: int
    progress: float


def earnings(now, settings):
    """Derive today's earned amount from the clock, including late app starts."""
    working_days = workdays(now.year, now.month, settings)
    monthly_salary = Decimal(settings["monthly"])
    daily_target = monthly_salary / working_days if working_days else Decimal(0)

    start_seconds = minutes(settings["start"]) * 60
    end_seconds = minutes(settings["end"]) * 60
    current_seconds = (
        now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    )
    elapsed = current_seconds - start_seconds
    duration = end_seconds - start_seconds
    progress = min(1.0, max(0.0, elapsed / duration))
    if not is_workday(now.date(), settings):
        progress = 0.0

    amount = daily_target * Decimal(str(progress))
    return Earnings(amount, daily_target, working_days, progress)


def load_settings():
    settings = dict(DEFAULTS, overrides={})
    try:
        settings.update(json.loads(CONFIG.read_text(encoding="utf-8")))
        if settings.get("theme") == "dopamine":
            settings["theme"] = "rose_dusk"
        validate(settings)
    except (OSError, ValueError, TypeError, KeyError, InvalidOperation):
        settings = dict(DEFAULTS, overrides={})
    return settings


def validate(settings):
    if settings["theme"] not in THEMES:
        raise ValueError("请选择有效的配色方案。")
    if type(settings["opacity"]) is not int or not 65 <= settings["opacity"] <= 100:
        raise ValueError("窗口不透明度须在 65%–100% 之间。")
    if type(settings["minimize_to_tray"]) is not bool:
        raise ValueError("最小化设置无效。")
    amount = Decimal(settings["monthly"])
    if not amount.is_finite() or amount <= 0 or amount > Decimal("1000000000"):
        raise ValueError("请输入大于 0 且不超过十亿元的月薪。")
    if minutes(settings["end"]) <= minutes(settings["start"]):
        raise ValueError("下班时间必须晚于上班时间（暂不支持跨夜班）。")
    if settings["rest"] not in ("单休", "双休") or settings["single_rest"] not in range(7):
        raise ValueError("休息日设置无效。")
    if not isinstance(settings["overrides"], dict):
        raise ValueError("日历设置无效。")
    for day, value in settings["overrides"].items():
        dt.date.fromisoformat(day)
        if type(value) is not bool:
            raise ValueError("日历设置无效。")
