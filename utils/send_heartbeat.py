import time
import logging
import requests
from utils.get_cpu_serial import get_cpu_serial  # 或者直接复制 get_cpu_serial 的实现

logger = logging.getLogger(__name__)


def send_heartbeat(
    activate_url: str,
    client_id: str,
    psw: str,
    timeout: int = 5
) -> tuple[bool, str]:
    """
    发送心跳包到服务器。
    :param activate_url: 接口地址，比如 ACTIVATE_URL
    :param client_id:    激活后获得的 CLIENT_ID
    :param psw:          激活后获得的 PSW
    :param timeout:      请求超时时间（秒）
    :returns:            (ok, message) 元组，ok 表示心跳是否成功
    """
    if not client_id:
        logger.debug("未设置 CLIENT_ID，跳过心跳")
        return False, 'no_client_id'

    try:
        cpu = get_cpu_serial()
        resp = requests.post(
            activate_url,
            data={'action': 'beat', 'ClientId': client_id, 'PSW': psw, 'CPU': cpu},
            timeout=timeout
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                data = {}
            ok = data.get('success', data.get('valid', False))
            msg = data.get('info', data.get('err', ''))
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f'心跳已发送，200 OK ({ts})')
            if not ok:
                logger.warning(f'心跳验证失败：{msg}')
            return ok, msg
        else:
            logger.warning(f'心跳失败，状态码：{resp.status_code}')
            return False, f'status_{resp.status_code}'
    except Exception as e:
        logger.error(f'心跳异常：{e}')
        return False, str(e)
