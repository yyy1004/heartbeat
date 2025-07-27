pyinstaller --noconfirm --windowed --onedir main.py
--onefile 会把所有资源打到一个自解包段，杀软常会拦截

 pyinstaller --noconfirm --windowed --onedir --hidden-import=ssl  --hidden-import=_ssl  main.py


 一、项目简介
该项目是一个名为 Heartbeat 的客户端工具，用于定期向指定服务器发送心跳信息，从而保持授权或激活状态。程序运行后会在系统托盘中常驻，并提供多个控制选项。

二、运行环境与依赖
仅支持 Windows 平台（通过 WMI 获取 CPU 序列号）。

需要 Python 3 环境，依赖的主要库包括：

requests

pystray

Pillow（用于托盘图标）

schedule

wmi

pythoncom

如需打包成可执行文件，可使用 PyInstaller。

三、安装和启动
直接运行源码

python main.py
程序启动后会自动在托盘区显示图标（初次运行需联网激活）。

打包为独立程序

参考 readme.txt 中的示例：

pyinstaller --noconfirm --windowed --onedir --hidden-import=ssl --hidden-import=_ssl main.py
打包配置可查看 main.spec。

四、配置文件和参数
默认配置来源
在 config.py 中定义了默认值。首次运行时会在用户目录 %APPDATA%\\Heartbeat\\config.json 生成配置文件：

{"host": "http://localhost:38519"}
host：服务器地址，不含 /ajax/... 后缀。

程序主要配置项

变量	含义	默认值/说明
ACTIVATE_URL	激活/心跳接口地址，等于 host + "/ajax/heartbeatHandler.ashx"	随 host 变化
VALIDATE_URL	授权验证接口地址，通常与 ACTIVATE_URL 相同	与 ACTIVATE_URL 相同
CLIENT_ID	激活成功后服务器返回的客户端标识符	None（首次激活后会保存）
PSW	激活成功后服务器返回的密码	None（首次激活后会保存）
heartbeat_interval	心跳间隔（秒）	15
MAX_AUTH_RETRIES	授权失败后的最大重试次数	30
MAX_LOG_FILES	最多保留的日志文件数量	3
LOG_DIR	日志文件保存目录（程序运行目录）	当前工作目录
file_logging_enabled	是否向文件写日志	True
配置修改方式

托盘菜单修改
在托盘菜单中选择“修改服务器”可更新 host，程序会自动重写 config.json。

手工编辑
也可以直接编辑 %APPDATA%\\Heartbeat\\config.json，调整服务器地址后重启程序。

五、使用说明
程序启动流程

启动时先尝试本地或远程授权（见 modules/auth.py）。

根据授权结果决定是否开启心跳功能，并在托盘图标中以绿色（正常）或灰色（暂停）显示。

托盘菜单功能（见 modules/tray.py）

当前状态：弹窗显示激活状态、心跳状态、当前间隔以及最近一次成功/失败时间。

暂停发送/继续发送：手动启停心跳。

日志输出：开/关：控制是否记录日志到文件（控制台日志仍保持）。

设置间隔：输入新的心跳时间间隔（5～3600 秒）。

修改服务器：更新服务器地址，重写 config.json。

退出：安全退出并停止托盘图标。

日志管理

每日创建一个以日期命名的日志文件，文件名格式如 YYYYMMDDheartbeat.log。
程序会在每日零点检测日期变化，若客户端持续运行将自动切换到新的日志文件。

通过 utils.log_utils 在每天凌晨清理旧日志，仅保留最多 MAX_LOG_FILES 个。

授权与心跳

启动后若无 CLIENT_ID，会向服务器发送 activate 请求获取授权。

正常情况下，心跳以设定间隔向服务器发送 beat 请求；若失败会自动重试授权。

六、常见问题
无法获取 CPU 序列号

程序依赖 WMI，如果权限不足或环境禁止 WMI 调用，会抛出异常（见 utils.get_cpu_serial.py）。

请确保以管理员权限运行，或者在允许 WMI 的环境下使用。

日志过多或未生成

检查 LOG_DIR 是否可写。

若超过 MAX_LOG_FILES，旧日志会被自动删除。

托盘图标不显示

需要确保安装了 pystray 与 Pillow 等库，并在支持托盘图标的桌面环境中运行。

上述内容即为该项目的使用说明与配置解释，供参考。如需进一步自定义，可查看源码中的各模块实现。