#!/usr/bin/env python3
"""Build the Linux package with system Python/Tk/GTK dependencies."""
import os
from pathlib import Path
import shutil
import subprocess

from common import BUILD, DIST, PACKAGE, ROOT, VERSION

os.umask(0o022)
stage = BUILD / "deb-root"
if stage.exists():
    shutil.rmtree(stage)


def write(path, content, mode=0o644):
    destination = stage / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    destination.chmod(mode)


write(
    "DEBIAN/control",
    f"""Package: salary-motivator
Version: {VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: WizzenH <81939519+WizzenH@users.noreply.github.com>
Depends: python3 (>= 3.8), python3-tk, python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1 | gir1.2-appindicator3-0.1
Recommends: fonts-noto-cjk
Description: Floating daily salary counter
 An always-on-top desktop widget with monthly salary, working calendar,
 eight color themes, opacity controls, tray integration and login startup.
""",
)
write("DEBIAN/conffiles", "/etc/xdg/autostart/salary-motivator.desktop\n")
shutil.copytree(
    PACKAGE,
    stage / "usr/share/salary-motivator/salary_motivator",
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
installed_package = stage / "usr/share/salary-motivator/salary_motivator"
installed_package.chmod(0o755)
for path in installed_package.rglob("*"):
    path.chmod(0o755 if path.is_dir() else 0o644)
write(
    "usr/bin/salary-motivator",
    """#!/usr/bin/python3
import sys
sys.path.insert(0, "/usr/share/salary-motivator")
from salary_motivator.app import main
main()
""",
    0o755,
)
entry = (ROOT / "packaging/linux/salary-motivator.desktop").read_text()
write("usr/share/applications/salary-motivator.desktop", entry)
write(
    "etc/xdg/autostart/salary-motivator.desktop",
    entry + "X-GNOME-Autostart-enabled=true\n",
)
write(
    "usr/share/icons/hicolor/scalable/apps/salary-motivator.svg",
    (PACKAGE / "assets/icon.svg").read_text(),
)
write("usr/share/doc/salary-motivator/README.md", (ROOT / "README.md").read_text())
write("usr/share/doc/salary-motivator/copyright", (ROOT / "LICENSE").read_text())
output = DIST / f"salary-motivator_{VERSION}_all.deb"
subprocess.run(
    ["dpkg-deb", "--root-owner-group", "--build", str(stage), str(output)], check=True
)
print(output)
