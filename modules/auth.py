import schedule

import config
from modules.tray import update_tray_status
from utils.activate import activate_once
from utils.validate import validate_remote


def retry_authorize():
    """授权失败后重试"""
    config.auth_retry_count += 1
    config.logger.info(f'授权重试第 {config.auth_retry_count} 次…')
    result = validate_remote(config.VALIDATE_URL, config.CLIENT_ID) if config.CLIENT_ID else activate_once(config.ACTIVATE_URL)
    ok = result.get('valid', result.get('success', False))
    if ok:
        config.heartbeat_enabled = True
        update_tray_status()
        if 'clientId' in result:
            config.CLIENT_ID = result['clientId']
            config.logger.info(f'已设置 CLIENT_ID = {config.CLIENT_ID}')
        if 'psw' in result:
            config.PSW = result['psw']
        config.logger.info('重试激活成功，恢复心跳')
        schedule.clear('auth_retry')
    elif config.auth_retry_count >= config.MAX_AUTH_RETRIES:
        config.logger.warning('重试次数已达上限，停止重试')
        schedule.clear('auth_retry')
    else:
        err = result.get('err', '')
        config.logger.info(f'重试激活失败，{err}')


def check_local_then_remote():
    """程序启动时，本地或远程授权流程"""

    try:
        if not config.CLIENT_ID:
            result = activate_once(config.ACTIVATE_URL)
            ok = result.get('success', False)
        else:
            result = validate_remote(config.VALIDATE_URL, config.CLIENT_ID)
            ok = result.get('valid', False)
        config.heartbeat_enabled = ok
        update_tray_status()
        err = result.get('err', '')
        config.logger.info(f'授权{"通过" if ok else f"失败，已暂停心跳, {err}"}')
        if 'clientId' in result:
            config.CLIENT_ID = result['clientId']
            config.logger.info(f'已设置 CLIENT_ID = {config.CLIENT_ID}')
        if 'psw' in result:
            config.PSW = result['psw']
        if not ok:
            config.auth_retry_count = 0
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')
    except Exception as e:
        config.logger.error('check_local_then_remote 异常：' + str(e))


def schedule_daily_validate():
    """每天 12:10 验证授权"""

    def job():
        result = validate_remote(config.VALIDATE_URL, config.CLIENT_ID)
        ok = result.get('valid', False)
        if ok:
            config.heartbeat_enabled = True
            update_tray_status()
            config.logger.info('每日授权验证通过')
        else:
            config.heartbeat_enabled = False
            update_tray_status()
            config.logger.warning('每日授权验证失败，已暂停心跳')
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')

    schedule.every().day.at('12:10').do(job)
