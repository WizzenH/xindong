# 第三方组件

项目自身以 MIT 许可证发布。Windows 安装包内置以下组件，其许可证不会因打包而改变：

- **CPython 3.13.12 x64**：来自 Python 官方发行 MSI，运行时根目录保留 `LICENSE.txt`。
- **Tcl / Tk**：来自 Python 的 `tcltk.msi`，原有许可证随运行时文件一起保留。
- **Microsoft Visual C++ runtime**：由官方 Python 发行组件携带，保留原分发内容。
- **NSIS**：用于构建安装器及卸载器，使用其发行版提供的安装器组件。

运行时官方目录：[Python 3.13.12 amd64](https://www.python.org/ftp/python/3.13.12/amd64/)。下载校验值见 `packaging/runtime-lock.json`。

Linux 包依赖发行版提供的 Python、Tk、GTK、PyGObject 和 AppIndicator，这些系统组件不复制到本项目的源码包中。
