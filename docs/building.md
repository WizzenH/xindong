# 构建与验证

Python 源码要求 3.8+。Windows 包使用固定的 Python 3.13.12 x64 运行时，组件与 SHA-256 存放于 `packaging/runtime-lock.json`。

## 本机环境

本项目约定：在这台开发机器上，源码构建和检查统一使用 `schroot -c 2503`。先检查仓库路径在 schroot 内的映射，再从该路径执行下列命令；不要混用宿主机和 schroot 的构建产物。默认独立目录为 `.build-2503/`。

schroot / Ubuntu 22.04 内的开发依赖：

```sh
sudo apt install python3-tk python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 fonts-noto-cjk xvfb xauth dbus-x11 openbox stalonetray xcompmgr libxtst6 black nsis msitools gcc-mingw-w64-x86-64 curl
```

以下命令均在约定的 schroot 仓库目录内执行。CI 使用隔离的 GitHub runner，依赖和命令保持一致。

## 检查

```sh
xvfb-run -a python3 tests/smoke_core.py
xvfb-run -a python3 tests/smoke_themes.py
dbus-run-session -- xvfb-run -a python3 tests/smoke_desktop.py
dbus-run-session -- xvfb-run -a python3 tests/smoke_indicator.py
black --check src tests scripts packaging
```

桌面测试会创建独立配置目录，启动自己的 Openbox、托盘宿主和合成器，并在结束时清理，不改动个人工资设置。

## 构建

```sh
python3 packaging/build_deb.py
python3 packaging/fetch_runtime.py
python3 packaging/build_windows.py
```

输出在 `dist/`。可用 `SALARY_BUILD_DIR` 与 `SALARY_DIST_DIR` 指定独立输出目录。

运行时先从 Python 官方站下载，失败时尝试镜像；每个组件必须匹配固定 SHA-256，构建脚本还会再次核验。

## 安装验证

在隔离的 schroot 中安装 deb 后，可指定已安装的包路径运行：

```sh
sudo dpkg -i dist/salary-motivator_1.2.0_all.deb
xvfb-run -a python3 tests/smoke_core.py /usr/share/salary-motivator
dbus-run-session -- xvfb-run -a python3 tests/smoke_desktop.py /usr/share/salary-motivator
sudo dpkg --purge salary-motivator
```

可选的 Windows 安装验证需要 Wine，运行时测试不编译宿主机源码：

```sh
xvfb-run -a python3 scripts/verify_wine.py --wine /path/to/wine
```

若 Wine 来自自带库的发行包，可额外指定 `--wineserver` 和 `--library-path`。测试仅操作 `.build-2503/test-prefix/`，不接触已有 Wine 前缀。

原生 Windows 仍需实际桌面试用。Wine 验证不能替代所有 Windows 发行版、缩放比例或桌面环境的测试。

## 截图与发布

```sh
xvfb-run -a -s '-screen 0 1280x2000x24' python3 scripts/preview_themes.py
python3 packaging/release_assets.py
```

正式发布由 `.github/workflows/release.yml` 完成：推送 `v*` 标签、以 `release: ` 开头的 main 分支发布提交，或手动执行工作流。工作流校验版本、运行检查，再构建安装包和校验文件，上传到 GitHub Release。普通提交只运行 CI。
