"""Register or inspect login startup using the current user's OS settings."""
import os
from pathlib import Path
import subprocess
import sys

from ..model import CONFIG_HOME, AUTOSTART_NAME

PACKAGE_DIRECTORY = Path(__file__).resolve().parents[1]


def startup_command():
    executable = Path(sys.executable)
    if os.name == "nt":
        launcher = PACKAGE_DIRECTORY.parent.parent / "SalaryMotivator.exe"
        if launcher.is_file():
            return [str(launcher)]
        windowed = executable.with_name("pythonw.exe")
        if windowed.is_file():
            executable = windowed
    elif PACKAGE_DIRECTORY.parent == Path("/usr/share/salary-motivator"):
        return ["/usr/bin/salary-motivator"]

    source_launcher = PACKAGE_DIRECTORY.parent.parent / "scripts/run.py"
    if PACKAGE_DIRECTORY.parent.name == "src" and source_launcher.is_file():
        return [str(executable), str(source_launcher)]
    return [str(executable), "-m", "salary_motivator"]


def autostart_enabled():
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            ) as key:
                return bool(winreg.QueryValueEx(key, "SalaryMotivator")[0])
        except FileNotFoundError:
            return False
    candidates = [CONFIG_HOME / "autostart" / AUTOSTART_NAME]
    candidates += [
        Path(folder) / "autostart" / AUTOSTART_NAME
        for folder in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":")
        if folder
    ]
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        lines = {line.strip().lower() for line in content.splitlines()}
        return (
            "hidden=true" not in lines
            and "x-gnome-autostart-enabled=false" not in lines
        )
    return False


def set_autostart(enabled):
    if os.name == "nt":
        import winreg

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    "SalaryMotivator",
                    0,
                    winreg.REG_SZ,
                    subprocess.list2cmdline(startup_command()),
                )
            else:
                try:
                    winreg.DeleteValue(key, "SalaryMotivator")
                except FileNotFoundError:
                    pass
        return
    path = CONFIG_HOME / "autostart" / AUTOSTART_NAME
    path.parent.mkdir(parents=True, exist_ok=True)

    def quote(value):
        value = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("`", "\\`")
            .replace("$", "\\$")
            .replace("%", "%%")
        )
        return '"' + value + '"'

    command = " ".join(quote(arg) for arg in startup_command())
    content = (
        "[Desktop Entry]\nType=Application\nName=Salary Motivator\n"
        "Name[zh_CN]=上班鼓励器\nExec="
        + command
        + "\nTryExec="
        + startup_command()[0]
        + "\nTerminal=false\n"
        "Hidden="
        + ("false" if enabled else "true")
        + "\nX-GNOME-Autostart-enabled="
        + ("true" if enabled else "false")
        + "\n"
    )
    temporary = path.with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
