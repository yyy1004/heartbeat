import os
import json
import time
import threading
import schedule
import logging
import tkinter as tk
from tkinter import simpledialog, messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

from utils.activate import activate_once
from utils.validate import validate_remote
from utils.send_heartbeat import send_heartbeat
from utils.save_host import save_host


# ====== 日志配置 ======
LOG_FILE = 'heartbeat.log'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
stream_handler = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(fmt)
stream_handler.setFormatter(fmt)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
file_logging_enabled = True  # 控制日志文件输出

# ====== 配置文件路径 ======
CONFIG_FILE = os.path.join(os.getenv('APPDATA'), 'Heartbeat', 'config.json')
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
_default_host = 'http://localhost:38519'

# ====== 授权配置 ======
CLIENT_ID = None
PSW = None

# 读取 host 配置
try:
    cfg = json.load(open(CONFIG_FILE, 'r', encoding='utf-8'))
    host = cfg.get('host', _default_host)
except Exception:
    host = _default_host

ACTIVATE_URL = f'{host}/ajax/heartbeatHandler.ashx'
VALIDATE_URL = ACTIVATE_URL

# ====== 心跳 & 重试 配置 ======
heartbeat_enabled = False
heartbeat_interval = 15  # 秒
last_success_time = None
last_failure_time = None
last_error_msg = ''
tray_icon = None

auth_retry_count = 0
MAX_AUTH_RETRIES = 30

# ====== 全局 Tk 实例 ======
_root = tk.Tk()
_root.withdraw()
_root.attributes('-topmost', True)


def retry_authorize():
    """授权失败后重试"""
    global auth_retry_count, heartbeat_enabled, CLIENT_ID, PSW
    auth_retry_count += 1
    logger.info(f'授权重试第 {auth_retry_count} 次…')
    result = validate_remote(VALIDATE_URL, CLIENT_ID) if CLIENT_ID else activate_once(ACTIVATE_URL)
    ok = result.get('valid', result.get('success', False))
    if ok:
        heartbeat_enabled = True
        if 'clientId' in result:
            CLIENT_ID = result['clientId']
            logger.info(f'已设置 CLIENT_ID = {CLIENT_ID}')
        if 'psw' in result:
            PSW = result['psw']
        logger.info('重试激活成功，恢复心跳')
        schedule.clear('auth_retry')
    elif auth_retry_count >= MAX_AUTH_RETRIES:
        logger.warning('重试次数已达上限，停止重试')
        schedule.clear('auth_retry')


def check_local_then_remote():
    """程序启动时，本地或远程授权流程"""
    global heartbeat_enabled, auth_retry_count, CLIENT_ID, PSW
    try:
        if not CLIENT_ID:
            result = activate_once(ACTIVATE_URL)
            ok = result.get('success', False)
        else:
            result = validate_remote(VALIDATE_URL, CLIENT_ID)
            ok = result.get('valid', False)
        heartbeat_enabled = ok
        logger.info(f'授权{"通过" if ok else "失败，已暂停心跳"}')
        if 'clientId' in result:
            CLIENT_ID = result['clientId']
            logger.info(f'已设置 CLIENT_ID = {CLIENT_ID}')
        if 'psw' in result:
            PSW = result['psw']
        if not ok:
            auth_retry_count = 0
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')
    except Exception as e:
        logger.error('check_local_then_remote 异常：' + str(e))


def schedule_daily_validate():
    """每天 12:10 验证授权"""
    def job():
        global heartbeat_enabled, CLIENT_ID
        result = validate_remote(VALIDATE_URL, CLIENT_ID)
        ok = result.get('valid', False)
        if ok:
            heartbeat_enabled = True
            logger.info('每日授权验证通过')
        else:
            heartbeat_enabled = False
            logger.warning('每日授权验证失败，已暂停心跳')
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')
    schedule.every().day.at('12:10').do(job)

def _send_and_record_heartbeat():
    """
    调用 utils/send_heartbeat.py 里的 send_heartbeat，
    并把成功/失败的时间戳、日志都更新到全局变量里。
    """
    global last_success_time, last_failure_time, last_error_msg

    ok = send_heartbeat(ACTIVATE_URL, CLIENT_ID, PSW)
    ts = time.strftime('%Y-%m-%d %H:%M:%S')

    if ok:
        last_success_time = ts
        last_error_msg    = ''
      #  logger.info(f'心跳已发送，200 OK ({ts})')
    # utils.send_heartbeat 已经记录成功日志，这里不再重复输出
    else:
        last_failure_time = ts
        last_error_msg    = '心跳发送失败'
        logger.warning(f'心跳失败 ({ts})')


def reschedule_heartbeat():
    """
    重设心跳调度：
      1. 先清掉旧的任务
      2. 立刻发送一次
      3. 按新的 heartbeat_interval 周期，反复调用 _send_and_record_heartbeat
    """
    schedule.clear('hb')

    # 1. 立即发送一次
    _send_and_record_heartbeat()

    # 2. 按新间隔周期调度
    schedule.every(heartbeat_interval).seconds.do(
        _send_and_record_heartbeat
    ).tag('hb')

    logger.info(f'心跳间隔已设置为 {heartbeat_interval} 秒')

def schedule_thread():
    """后台调度线程"""
    while True:
        schedule.run_pending()
        time.sleep(1)


def create_icon(color):
    """生成托盘图标"""
    img = Image.new('RGB', (64, 64), color)
    dc = ImageDraw.Draw(img)
    dc.ellipse((16, 16, 48, 48), fill='white')
    return img

icon_green = create_icon('green')
icon_red   = create_icon('red')
icon_gray  = create_icon('gray')

# ====== 主线程 UI 相关函数 ======

def check_password_dialog():
    pwd = simpledialog.askstring('验证', '请输入操作密码：', show='*', parent=_root)
    if PSW and pwd == PSW:
        return True
    if PSW:
        messagebox.showerror('密码错误', '操作已取消', parent=_root)
    return False


def _modify_server_dialog():
    global ACTIVATE_URL, VALIDATE_URL

    if PSW and not check_password_dialog():
        return

    # 现在安全地读取 ACTIVATE_URL 来做 initialvalue
    prev_host = ACTIVATE_URL.rsplit('/ajax', 1)[0]
    new_host = simpledialog.askstring(
        '修改服务器',
        '请输入新服务器地址：',
        initialvalue=prev_host,
        parent=_root
    )

    if new_host:
        # 调用你封装好的 utils/save_host.py
        host_url, activate_url = save_host(CONFIG_FILE, new_host)

        # 修改全局变量
        ACTIVATE_URL = activate_url
        VALIDATE_URL = activate_url

        messagebox.showinfo('修改成功', f'服务器地址已更新为：{host_url}', parent=_root)


def modify_server(icon, item):
    _root.after(0, _modify_server_dialog)


def _toggle_heartbeat_dialog():
    if PSW and not check_password_dialog():
        return
    global heartbeat_enabled
    heartbeat_enabled = not heartbeat_enabled
    logger.info('心跳' + ('开启' if heartbeat_enabled else '暂停'))


def toggle_heartbeat(icon, item):
    _root.after(0, _toggle_heartbeat_dialog)


def _toggle_logging_dialog():
    if PSW and not check_password_dialog():
        return
    global file_logging_enabled
    file_logging_enabled = not file_logging_enabled
    if file_logging_enabled:
        logger.addHandler(file_handler)
    else:
        logger.removeHandler(file_handler)
    logger.info('日志输出' + ('启用' if file_logging_enabled else '禁用'))


def toggle_logging(icon, item):
    _root.after(0, _toggle_logging_dialog)


def _set_interval_dialog():
    if PSW and not check_password_dialog():
        return
    global heartbeat_interval
    val = simpledialog.askinteger(
        '设置间隔', '请输入心跳间隔（秒）',
        initialvalue=heartbeat_interval, minvalue=5, maxvalue=3600,
        parent=_root
    )
    if val:
        heartbeat_interval = val
        reschedule_heartbeat()


def set_interval(icon, item):
    _root.after(0, _set_interval_dialog)


def _show_status_dialog():
    lines = [
        f"激活：{'正常' if heartbeat_enabled else '未激活'}",
        f"心跳：{'已开启' if heartbeat_enabled else '已暂停'}",
        f"间隔：{heartbeat_interval} 秒"
    ]
    if last_success_time:
        lines.append("最近成功：" + last_success_time)
    if last_failure_time:
        lines.append("最近失败：" + last_failure_time)
    if last_error_msg:
        lines.append("错误信息：" + last_error_msg)
    msg = "\n".join(lines)
    messagebox.showinfo('当前状态', msg, parent=_root)


def show_status(icon, item):
    _root.after(0, _show_status_dialog)


def _require_exit_dialog():
    if PSW and not check_password_dialog():
        return
    logger.info('退出程序')
    tray_icon.stop()
    os._exit(0)


def require_exit(icon, item):
    _root.after(0, _require_exit_dialog)


def setup_tray():
    """初始化并运行托盘图标"""
    global tray_icon
    tray_icon = Icon('Heartbeat')
    tray_icon.icon  = icon_green
    tray_icon.title = '心跳客户端'
    tray_icon.menu  = Menu(
        MenuItem('当前状态', show_status),
        MenuItem(lambda _: '暂停发送' if heartbeat_enabled else '继续发送', toggle_heartbeat),
        MenuItem(lambda _: '日志输出：开' if file_logging_enabled else '日志输出：关', toggle_logging),
        MenuItem('设置间隔', set_interval),
        MenuItem('修改服务器', modify_server),
        MenuItem('退出', require_exit),
    )
    tray_icon.run()

if __name__ == '__main__':
    check_local_then_remote()
    schedule_daily_validate()
    reschedule_heartbeat()
    threading.Thread(target=schedule_thread, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()
    _root.mainloop()
