import os
import json
import threading
import schedule
import logging
import tkinter as tk
import time

from utils.send_heartbeat import send_heartbeat

from modules.auth import check_local_then_remote, schedule_daily_validate
from modules.tray import setup_tray


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


if __name__ == '__main__':
    check_local_then_remote()
    schedule_daily_validate()
    reschedule_heartbeat()
    threading.Thread(target=schedule_thread, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()
    _root.mainloop()
