import threading

import config
from modules.auth import check_local_then_remote
from modules.tray import setup_tray
from modules.heartbeat import reschedule_heartbeat, schedule_thread
from utils.log_utils import schedule_log_cleanup, schedule_log_rotation


if __name__ == '__main__':
    check_local_then_remote()
    reschedule_heartbeat()
    schedule_log_cleanup(
        config.LOG_DIR,
        'heartbeat.log',
        config.MAX_LOG_FILES,
        config.logger,
    )
    schedule_log_rotation()
    threading.Thread(target=schedule_thread, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()
    config._root.mainloop()
