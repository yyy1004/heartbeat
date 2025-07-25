import logging
import requests
from typing import Optional
from utils.get_cpu_serial import get_cpu_serial

logger = logging.getLogger(__name__)


def validate_remote(validate_url: str,
                    client_id: Optional[str],
                    timeout: int = 5) -> dict:
    """
    向服务器验证授权是否有效。
    :param validate_url: 授权验证接口地址（通常等于 ACTIVATE_URL）
    :param client_id: 上次激活时拿到的 CLIENT_ID
    :param timeout: 请求超时（秒）
    :return: 服务器返回的 JSON（包含 'valid': bool 等字段）
    """
    cpu = get_cpu_serial()
    if not client_id:
        return {'valid': False}

    try:
        resp = requests.post(
            validate_url,
            data={'action': 'validate', 'ClientId': client_id, 'CPU': cpu},
            timeout=timeout
        )
        return resp.json()
    except Exception as e:
        logger.error('validate_remote 异常：%s', e)
        return {'valid': False}