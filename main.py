import threading

import config
from modules.auth import check_local_then_remote
from modules.tray import setup_tray
from modules.heartbeat import reschedule_heartbeat, schedule_thread


if __name__ == '__main__':
    check_local_then_remote()
    reschedule_heartbeat()
    threading.Thread(target=schedule_thread, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()
    config._root.mainloop()
