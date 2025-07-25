import json
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def save_host(config_file: str, new_host: str) -> Tuple[str, str]:
    """
    保存并应用新的服务器地址到配置文件。

    :param config_file: config.json 的完整路径
    :param new_host:    用户输入的新服务器地址（可以带或不带尾部斜杠）
    :returns:           两个值 (host_url, activate_url)
                        host_url:  去掉末尾 '/' 的 new_host
                        activate_url: 格式化后的激活 URL
    """
    # 去掉末尾多余的 '/'
    host_url = new_host.rstrip('/')
    # 写入 JSON
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump({'host': host_url}, f)
    # 生成接口地址
    activate_url = f'{host_url}/ajax/heartbeatHandler.ashx'
    logger.info(f'已更新服务器地址为：{host_url}')
    return host_url, activate_url