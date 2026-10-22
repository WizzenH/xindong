"""Theme preview, cancel/save and migration checks with isolated settings."""
import os
from pathlib import Path
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))


def luminance(color):
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return sum(
        value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722))
    )


def contrast(first, second):
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


with tempfile.TemporaryDirectory(prefix="salary-themes-") as temporary:
    os.environ["XDG_CONFIG_HOME"] = temporary
    os.environ["XDG_CONFIG_DIRS"] = temporary
    from salary_motivator import model as payroll
    from salary_motivator.app import SalaryWidget
    from salary_motivator.themes import THEMES

    old_settings = dict(payroll.DEFAULTS, monthly="12345", overrides={})
    old_settings.pop("theme")
    payroll.CONFIG.parent.mkdir(parents=True)
    import json

    payroll.CONFIG.write_text(json.dumps(old_settings))
    assert payroll.load_settings()["theme"] == "night"
    assert payroll.load_settings()["monthly"] == "12345"

    # Removing a preview theme must not reset the user's salary/calendar.
    removed_theme = dict(old_settings, theme="dopamine")
    payroll.CONFIG.write_text(json.dumps(removed_theme))
    migrated = payroll.load_settings()
    assert migrated["theme"] == "rose_dusk"
    assert migrated["monthly"] == "12345"
    payroll.CONFIG.write_text(json.dumps(old_settings))

    app = SalaryWidget()
    try:
        for key, theme in THEMES.items():
            # Check readability of the small labels as well as the headline amount.
            for role in ("foreground", "muted", "positive"):
                ratio = contrast(getattr(theme, role), theme.background)
                assert ratio >= 4.5, f"{key}/{role} contrast is only {ratio:.2f}"
            # The headline remains bold and >= 25 pt, so large-text contrast applies.
            assert contrast(theme.money, theme.background) >= 3
            assert contrast(theme.foreground, theme.surface) >= 4.5
            assert contrast(theme.work_foreground, theme.work_background) >= 4.5
            assert contrast(theme.accent_foreground, theme.accent) >= 4.5

            app.settings()
            dialog = app.dialog
            dialog.notebook.select(dialog.appearance)
            dialog.form["monthly"].set("23456")
            dialog.appearance.cards[key][1].invoke()
            app.root.update()
            assert app.theme.key == key
            assert app.canvas.cget("background").lower() == theme.background.lower()
            assert (
                app.canvas.itemcget(app.money_id, "fill").lower() == theme.money.lower()
            )
            assert dialog.form["monthly"].get() == "23456"
            assert (
                app.style.lookup("TLabel", "foreground").lower()
                == theme.foreground.lower()
            )
            dialog.cancel()
            assert app.theme.key == "night"
            assert payroll.load_settings()["monthly"] == "12345"

        # Commit a light theme with a calendar edit, then reopen to check persistence.
        app.settings()
        dialog = app.dialog
        dialog.form["monthly"].set("23456")
        dialog.appearance.cards["morandi"][1].invoke()
        import datetime as dt

        chosen_day = dt.date(dialog.year, dialog.month, 1)
        dialog.toggle_workday(chosen_day)
        dialog.save()
        saved = payroll.load_settings()
        assert saved["theme"] == "morandi"
        assert saved["monthly"] == "23456"
        assert chosen_day.isoformat() in saved["overrides"]
        app.settings()
        assert app.dialog.appearance.theme_key.get() == "morandi"
        app.dialog.appearance.cards["rose_dusk"][1].invoke()
        app.dialog.cancel()
        assert app.theme.key == "morandi"
        assert payroll.load_settings()["theme"] == "morandi"
        print(
            "PASS: eight palettes, body text >= 4.5:1 / headline >= 3:1, live preview, cancel/save, salary/calendar edits, legacy config migration"
        )
    finally:
        app.quit()
