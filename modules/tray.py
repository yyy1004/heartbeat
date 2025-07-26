import os
from tkinter import simpledialog, messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

import config
from modules.heartbeat import reschedule_heartbeat


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


def update_tray_status():
    """根据心跳状态更新托盘颜色和菜单"""
    if not config.tray_icon:
        return
    config.tray_icon.icon = icon_green if config.heartbeat_enabled else icon_gray
    config.tray_icon.update_menu()


def check_password_dialog():
    """弹出密码验证对话框，返回用户输入是否正确"""
    pwd = simpledialog.askstring('验证', '请输入操作密码：', show='*', parent=config._root)
    if config.PSW and pwd == config.PSW:
        return True
    if config.PSW:
        messagebox.showerror('密码错误', '操作已取消', parent=config._root)
    return False


def _modify_server_dialog():
    """让用户输入新的服务器地址并保存"""
    if config.PSW and not check_password_dialog():
        return
    prev_host = config.ACTIVATE_URL.rsplit('/ajax', 1)[0]
    new_host = simpledialog.askstring(
        '修改服务器',
        '请输入新服务器地址：',
        initialvalue=prev_host,
        parent=config._root
    )
    if new_host:
        from utils.save_host import save_host
        host_url, activate_url = save_host(config.CONFIG_FILE, new_host)
        config.ACTIVATE_URL = activate_url
        config.VALIDATE_URL = activate_url
        messagebox.showinfo('修改成功', f'服务器地址已更新为：{host_url}', parent=config._root)


def modify_server(icon, item):
    """在主线程中弹出修改服务器地址的窗口"""
    config._root.after(0, _modify_server_dialog)


def _toggle_heartbeat_dialog():
    """切换心跳发送状态"""
    if config.PSW and not check_password_dialog():
        return
    config.heartbeat_enabled = not config.heartbeat_enabled
    if config.heartbeat_enabled:
        config.auth_retry_count = 0
    config.logger.info('心跳' + ('开启' if config.heartbeat_enabled else '暂停'))
    update_tray_status()


def toggle_heartbeat(icon, item):
    """在主线程中切换心跳发送"""
    config._root.after(0, _toggle_heartbeat_dialog)


def _toggle_logging_dialog():
    """切换日志文件输出开关"""
    if config.PSW and not check_password_dialog():
        return
    config.file_logging_enabled = not config.file_logging_enabled
    if config.file_logging_enabled:
        config.logger.addHandler(config.file_handler)
    else:
        config.logger.removeHandler(config.file_handler)
    config.logger.info('日志输出' + ('启用' if config.file_logging_enabled else '禁用'))
    update_tray_status()


def toggle_logging(icon, item):
    """在主线程中切换日志输出"""
    config._root.after(0, _toggle_logging_dialog)


def _set_interval_dialog():
    """询问用户新的心跳间隔并生效"""
    if config.PSW and not check_password_dialog():
        return
    val = simpledialog.askinteger(
        '设置间隔', '请输入心跳间隔（秒）',
        initialvalue=config.heartbeat_interval, minvalue=5, maxvalue=3600,
        parent=config._root
    )
    if val:
        config.heartbeat_interval = val
        reschedule_heartbeat()


def set_interval(icon, item):
    """在主线程中修改心跳间隔"""
    config._root.after(0, _set_interval_dialog)


def _show_status_dialog():
    """弹出窗口显示当前心跳状态"""
    lines = [
        f"激活：{'正常' if config.heartbeat_enabled else '未激活'}",
        f"心跳：{'已开启' if config.heartbeat_enabled else '已暂停'}",
        f"间隔：{config.heartbeat_interval} 秒"
    ]
    if config.last_success_time:
        lines.append('最近成功：' + config.last_success_time)
    if config.last_failure_time:
        lines.append('最近失败：' + config.last_failure_time)
    if config.last_error_msg:
        lines.append('错误信息：' + config.last_error_msg)
    msg = "\n".join(lines)
    messagebox.showinfo('当前状态', msg, parent=config._root)


def show_status(icon, item):
    """在主线程中显示状态窗口"""
    config._root.after(0, _show_status_dialog)


def _require_exit_dialog():
    """退出程序前的清理操作"""
    if config.PSW and not check_password_dialog():
        return
    config.logger.info('退出程序')
    config.tray_icon.stop()
    os._exit(0)


def require_exit(icon, item):
    """在主线程中执行退出"""
    config._root.after(0, _require_exit_dialog)


def setup_tray():
    """创建并运行系统托盘图标及其菜单"""
    config.tray_icon = Icon('Heartbeat')
    config.tray_icon.icon = icon_green if config.heartbeat_enabled else icon_gray
    config.tray_icon.title = '心跳客户端'
    config.tray_icon.menu = Menu(
        MenuItem('当前状态', show_status),
        MenuItem(lambda _: '暂停发送' if config.heartbeat_enabled else '继续发送', toggle_heartbeat),
        MenuItem(lambda _: '日志输出：开' if config.file_logging_enabled else '日志输出：关', toggle_logging),
        MenuItem('设置间隔', set_interval),
        MenuItem('修改服务器', modify_server),
        MenuItem('退出', require_exit),
    )
    update_tray_status()
    config.tray_icon.run()
