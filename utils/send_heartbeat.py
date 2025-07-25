import time
import logging
import requests

logger = logging.getLogger(__name__)


def send_heartbeat(
    activate_url: str,
    client_id: str,
    psw: str,
    timeout: int = 5
) -> bool:
    """
    发送心跳包到服务器。
    :param activate_url: 接口地址，比如 ACTIVATE_URL
    :param client_id:    激活后获得的 CLIENT_ID
    :param psw:          激活后获得的 PSW
    :param timeout:      请求超时时间（秒）
    :returns:            True 表示 200 OK，False 表示失败
    """
    if not client_id:
        logger.debug("未设置 CLIENT_ID，跳过心跳")
        return False

    try:
        resp = requests.post(
            activate_url,
            data={'action': 'beat', 'ClientId': client_id, 'PSW': psw},
            timeout=timeout
        )
        if resp.status_code == 200:
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f'心跳已发送，200 OK ({ts})')
            return True
        else:
            logger.warning(f'心跳失败，状态码：{resp.status_code}')
            return False
    except Exception as e:
        logger.error(f'心跳异常：{e}')
        return False
