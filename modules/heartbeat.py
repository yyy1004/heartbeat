import time
import schedule

from utils.send_heartbeat import send_heartbeat


# ====== Heartbeat scheduling functions ======

def _send_and_record_heartbeat():
    """Send heartbeat and record timestamps"""
    import __main__ as main

    ok = send_heartbeat(main.ACTIVATE_URL, main.CLIENT_ID, main.PSW)
    ts = time.strftime('%Y-%m-%d %H:%M:%S')

    if ok:
        main.last_success_time = ts
        main.last_error_msg = ''
    else:
        main.last_failure_time = ts
        main.last_error_msg = '心跳发送失败'
        main.logger.warning(f'心跳失败 ({ts})')


def reschedule_heartbeat():
    """Clear old schedule, send once immediately and reschedule"""
    import __main__ as main

    schedule.clear('hb')
    _send_and_record_heartbeat()
    schedule.every(main.heartbeat_interval).seconds.do(
        _send_and_record_heartbeat
    ).tag('hb')
    main.logger.info(f'心跳间隔已设置为 {main.heartbeat_interval} 秒')


def schedule_thread():
    """Background thread to run scheduled jobs"""
    while True:
        schedule.run_pending()
        time.sleep(1)
