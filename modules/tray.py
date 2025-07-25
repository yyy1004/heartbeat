import os
from tkinter import simpledialog, messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw


# ====== 托盘相关函数 ======

def create_icon(color):
    """生成托盘图标"""
    img = Image.new('RGB', (64, 64), color)
    dc = ImageDraw.Draw(img)
    dc.ellipse((16, 16, 48, 48), fill='white')
    return img


icon_green = create_icon('green')
icon_red = create_icon('red')
icon_gray = create_icon('gray')


def check_password_dialog():
    import __main__ as main
    pwd = simpledialog.askstring('验证', '请输入操作密码：', show='*', parent=main._root)
    if main.PSW and pwd == main.PSW:
        return True
    if main.PSW:
        messagebox.showerror('密码错误', '操作已取消', parent=main._root)
    return False


def _modify_server_dialog():
    import __main__ as main
    if main.PSW and not check_password_dialog():
        return
    prev_host = main.ACTIVATE_URL.rsplit('/ajax', 1)[0]
    new_host = simpledialog.askstring(
        '修改服务器',
        '请输入新服务器地址：',
        initialvalue=prev_host,
        parent=main._root
    )
    if new_host:
        from utils.save_host import save_host
        host_url, activate_url = save_host(main.CONFIG_FILE, new_host)
        main.ACTIVATE_URL = activate_url
        main.VALIDATE_URL = activate_url
        messagebox.showinfo('修改成功', f'服务器地址已更新为：{host_url}', parent=main._root)


def modify_server(icon, item):
    import __main__ as main
    main._root.after(0, _modify_server_dialog)


def _toggle_heartbeat_dialog():
    import __main__ as main
    if main.PSW and not check_password_dialog():
        return
    main.heartbeat_enabled = not main.heartbeat_enabled
    main.logger.info('心跳' + ('开启' if main.heartbeat_enabled else '暂停'))


def toggle_heartbeat(icon, item):
    import __main__ as main
    main._root.after(0, _toggle_heartbeat_dialog)


def _toggle_logging_dialog():
    import __main__ as main
    if main.PSW and not check_password_dialog():
        return
    main.file_logging_enabled = not main.file_logging_enabled
    if main.file_logging_enabled:
        main.logger.addHandler(main.file_handler)
    else:
        main.logger.removeHandler(main.file_handler)
    main.logger.info('日志输出' + ('启用' if main.file_logging_enabled else '禁用'))


def toggle_logging(icon, item):
    import __main__ as main
    main._root.after(0, _toggle_logging_dialog)


def _set_interval_dialog():
    import __main__ as main
    if main.PSW and not check_password_dialog():
        return
    val = simpledialog.askinteger(
        '设置间隔', '请输入心跳间隔（秒）',
        initialvalue=main.heartbeat_interval, minvalue=5, maxvalue=3600,
        parent=main._root
    )
    if val:
        main.heartbeat_interval = val
        main.reschedule_heartbeat()


def set_interval(icon, item):
    import __main__ as main
    main._root.after(0, _set_interval_dialog)


def _show_status_dialog():
    import __main__ as main
    lines = [
        f"激活：{'正常' if main.heartbeat_enabled else '未激活'}",
        f"心跳：{'已开启' if main.heartbeat_enabled else '已暂停'}",
        f"间隔：{main.heartbeat_interval} 秒"
    ]
    if main.last_success_time:
        lines.append('最近成功：' + main.last_success_time)
    if main.last_failure_time:
        lines.append('最近失败：' + main.last_failure_time)
    if main.last_error_msg:
        lines.append('错误信息：' + main.last_error_msg)
    msg = "\n".join(lines)
    messagebox.showinfo('当前状态', msg, parent=main._root)


def show_status(icon, item):
    import __main__ as main
    main._root.after(0, _show_status_dialog)


def _require_exit_dialog():
    import __main__ as main
    if main.PSW and not check_password_dialog():
        return
    main.logger.info('退出程序')
    main.tray_icon.stop()
    os._exit(0)


def require_exit(icon, item):
    import __main__ as main
    main._root.after(0, _require_exit_dialog)


def setup_tray():
    import __main__ as main
    main.tray_icon = Icon('Heartbeat')
    main.tray_icon.icon = icon_green
    main.tray_icon.title = '心跳客户端'
    main.tray_icon.menu = Menu(
        MenuItem('当前状态', show_status),
        MenuItem(lambda _: '暂停发送' if main.heartbeat_enabled else '继续发送', toggle_heartbeat),
        MenuItem(lambda _: '日志输出：开' if main.file_logging_enabled else '日志输出：关', toggle_logging),
        MenuItem('设置间隔', set_interval),
        MenuItem('修改服务器', modify_server),
        MenuItem('退出', require_exit),
    )
    main.tray_icon.run()