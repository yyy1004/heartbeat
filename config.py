import os
import json
import tkinter as tk
import logging
from utils.log_utils import setup_log_file

# ====== 日志配置 ======
logger = logging.getLogger()
logger.setLevel(logging.INFO)
MAX_LOG_FILES = 3
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE, file_handler = setup_log_file(
    LOG_DIR, 'heartbeat.log', MAX_LOG_FILES, logger
)
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
