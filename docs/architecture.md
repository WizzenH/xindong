# 源码结构

项目采用 `src` 布局，程序、验证、构建和文档分别放在独立目录。生成的安装包和构建环境不进入 Git。

| 模块 | 职责 |
| --- | --- |
| `src/salary_motivator/__init__.py` | 唯一版本号，不加载 GUI |
| `app.py` | 主窗口绘制、定时刷新、窗口生命周期与托盘命令处理 |
| `model.py` | 工资计算、工作日判断、配置校验和原子写入，不依赖 Tk |
| `themes.py` | 八套不可变的 `Theme` 数据与颜色角色 |
| `ui/preferences.py` | 工资与日历草稿、保存与取消 |
| `ui/appearance.py` | 配色卡片、透明度和启动选项 |
| `platform/autostart.py` | 当前用户的登录启动项 |
| `platform/single_instance.py` | 防止重复启动的进程锁 |
| `platform/tray.py` | Windows 通知图标和 Linux GTK/AppIndicator 托盘 |
| `platform/window_chrome.py` | 保留系统管理能力的无边框处理 |
| `tests/` | 计算、主题、XEmbed/AppIndicator 和 Windows 交互验证 |
| `packaging/` | 可重复执行的 deb / exe 构建及运行时校验 |

## 数据流

1. 启动读取配置，通过默认值补齐旧配置缺少的字段。
2. 定时器把系统时间交给 `model.earnings()`，得到具名的 `Earnings`。
3. `render_earnings()` 更新界面；渲染与调度分离，可用同一时刻生成配色对照图。
4. 设置窗口维护独立草稿，配色与透明度仅预览，保存才写入配置，取消恢复已保存外观。

托盘回调只往队列发送命令，由 Tk 主线程操作窗口。Linux GTK 托盘运行在独立进程，避免在同一个线程混用两个 GUI 事件循环。

## 修改约定

- 新配色只修改 `themes.py`，保持持久化 `key` 稳定，卡片自动从集合生成。
- 颜色按作用命名，不在工资逻辑中零散写颜色常量。
- 工资规则只修改 `model.py`，保持它可独立于桌面环境检查。
- 系统差异放在 `platform/`，不把 Win32 / D-Bus 调用写进设置界面。
- 使用 Black 的 Python 3.8 格式；大段嵌套回调改成具名方法。
- 版本号只改 `__init__.py`，构建脚本从同一位置读取。

旧预览配色 `dopamine` 在加载时迁移到 `rose_dusk`，保留工资和日历设置。
