import schedule
from utils.activate import activate_once
from utils.validate import validate_remote


def retry_authorize():
    """授权失败后重试"""
    import __main__ as main

    main.auth_retry_count += 1
    main.logger.info(f'授权重试第 {main.auth_retry_count} 次…')
    result = validate_remote(main.VALIDATE_URL, main.CLIENT_ID) if main.CLIENT_ID else activate_once(main.ACTIVATE_URL)
    ok = result.get('valid', result.get('success', False))
    if ok:
        main.heartbeat_enabled = True
        if 'clientId' in result:
            main.CLIENT_ID = result['clientId']
            main.logger.info(f'已设置 CLIENT_ID = {main.CLIENT_ID}')
        if 'psw' in result:
            main.PSW = result['psw']
        main.logger.info('重试激活成功，恢复心跳')
        schedule.clear('auth_retry')
    elif main.auth_retry_count >= main.MAX_AUTH_RETRIES:
        main.logger.warning('重试次数已达上限，停止重试')
        schedule.clear('auth_retry')


def check_local_then_remote():
    """程序启动时，本地或远程授权流程"""
    import __main__ as main

    try:
        if not main.CLIENT_ID:
            result = activate_once(main.ACTIVATE_URL)
            ok = result.get('success', False)
        else:
            result = validate_remote(main.VALIDATE_URL, main.CLIENT_ID)
            ok = result.get('valid', False)
        main.heartbeat_enabled = ok
        main.logger.info(f'授权{"通过" if ok else "失败，已暂停心跳"}')
        if 'clientId' in result:
            main.CLIENT_ID = result['clientId']
            main.logger.info(f'已设置 CLIENT_ID = {main.CLIENT_ID}')
        if 'psw' in result:
            main.PSW = result['psw']
        if not ok:
            main.auth_retry_count = 0
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')
    except Exception as e:
        main.logger.error('check_local_then_remote 异常：' + str(e))


def schedule_daily_validate():
    """每天 12:10 验证授权"""
    import __main__ as main

    def job():
        result = validate_remote(main.VALIDATE_URL, main.CLIENT_ID)
        ok = result.get('valid', False)
        if ok:
            main.heartbeat_enabled = True
            main.logger.info('每日授权验证通过')
        else:
            main.heartbeat_enabled = False
            main.logger.warning('每日授权验证失败，已暂停心跳')
            schedule.every(20).seconds.do(retry_authorize).tag('auth_retry')

    schedule.every().day.at('12:10').do(job)
