import requests
import logging
from utils.get_cpu_serial import get_cpu_serial  # 或者直接复制 get_cpu_serial 的实现

logger = logging.getLogger(__name__)


def activate_once(activate_url, timeout=5):
    """
    通用的“激活”函数：
      · activate_url：服务器激活接口地址，比如 ACTIVATE_URL
      · timeout：请求超时时间（秒）
    返回值是服务器的 JSON 响应（dict）。
    """
    cpu = get_cpu_serial()
    try:
        resp = requests.post(activate_url, data={'action': 'activate', 'CPU': cpu}, timeout=timeout)
        return resp.json()
    except Exception as e:
        logger.error('activate_once 异常：' + str(e))
        return {'success': False}
