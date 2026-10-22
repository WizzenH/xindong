"""Regression checks using isolated configuration; no personal settings touched."""
import datetime as dt
import os
from pathlib import Path
import tempfile
import sys

with tempfile.TemporaryDirectory(prefix="salary-check-") as temporary:
    os.environ["XDG_CONFIG_HOME"] = temporary
    os.environ["XDG_CONFIG_DIRS"] = str(Path(temporary) / "system")
    package_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "src"
    )
    sys.path.insert(0, str(package_path))
    from salary_motivator import app as m, model as payroll
    from salary_motivator.platform import autostart as startup

    if len(sys.argv) > 1:
        assert startup.startup_command() == ["/usr/bin/salary-motivator"]
        assert Path("/etc/xdg/autostart/salary-motivator.desktop").exists()
    s = dict(payroll.DEFAULTS, overrides={})
    assert payroll.workdays(2026, 10, s) == 22
    assert payroll.workdays(2024, 2, s) == 21
    for hour, minute, expected in [
        (8, 0, 0),
        (8, 30, 0),
        (13, 0, 0.5),
        (17, 30, 1),
        (20, 0, 1),
    ]:
        assert (
            payroll.earnings(dt.datetime(2026, 10, 22, hour, minute), s)[3] == expected
        )
    assert payroll.earnings(dt.datetime(2026, 10, 24, 13), s)[0] == 0
    s["overrides"]["2026-10-24"] = True
    assert payroll.workdays(2026, 10, s) == 23
    s["rest"] = "单休"
    s["overrides"] = {}
    assert payroll.workdays(2026, 10, s) == 27
    global_file = Path(temporary) / "system/autostart" / payroll.AUTOSTART_NAME
    global_file.parent.mkdir(parents=True)
    global_file.write_text("[Desktop Entry]\nType=Application\nExec=salary-motivator\n")
    assert startup.autostart_enabled()
    startup.set_autostart(False)
    assert not startup.autostart_enabled()
    startup.set_autostart(True)
    assert startup.autostart_enabled()
    assert m.acquire_instance()
    assert not m.acquire_instance()
    app = m.SalaryWidget()
    app.root.update()
    app.settings()
    app.root.update()
    assert app.dialog.winfo_exists()
    app.dialog.destroy()
    app.root.destroy()
print(
    "PASS: salary boundaries, calendars, startup enable/disable, duplicate launch, GUI"
)
