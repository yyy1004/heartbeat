import time
import schedule

import config
from modules.auth import validate_and_update
from utils.send_heartbeat import send_heartbeat


# ====== Heartbeat scheduling functions ======

def _send_and_record_heartbeat():
    """Send heartbeat and record timestamps"""
    if not config.heartbeat_enabled:
        config.logger.debug('心跳已暂停，跳过发送')
        return

    ok, msg = send_heartbeat(config.ACTIVATE_URL, config.CLIENT_ID, config.PSW)
    ts = time.strftime('%Y-%m-%d %H:%M:%S')

    if ok:
        config.last_success_time = ts
        config.last_error_msg = ''
    else:
        config.last_failure_time = ts
        config.last_error_msg = msg or '心跳验证失败'
        config.logger.warning(f'心跳失败 ({ts})')
        validate_and_update()


def reschedule_heartbeat():
    """Clear old schedule, send once immediately and reschedule"""
    schedule.clear('hb')
    _send_and_record_heartbeat()
    schedule.every(config.heartbeat_interval).seconds.do(
        _send_and_record_heartbeat
    ).tag('hb')
    config.logger.info(f'心跳间隔已设置为 {config.heartbeat_interval} 秒')


def schedule_thread():
    """Background thread to run scheduled jobs"""
    while True:
        schedule.run_pending()
        time.sleep(1)
