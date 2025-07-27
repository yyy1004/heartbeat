import os
import glob
import logging
from datetime import datetime
import schedule
from typing import Optional


def setup_log_file(
    log_dir: str,
    suffix: str,
    max_files: int,
    logger: Optional[logging.Logger] = None,
) -> tuple[str, logging.FileHandler]:
    """Create dated log file and clean old ones."""
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f"{date_str}{suffix}")
    handler = logging.FileHandler(log_file, encoding='utf-8')
    clean_old_logs(log_dir, suffix, max_files, logger)
    return log_file, handler


def clean_old_logs(
    log_dir: str,
    suffix: str,
    max_files: int,
    logger: Optional[logging.Logger] = None,
) -> None:
    if logger is None:
        logger = logging.getLogger()
    pattern = os.path.join(log_dir, f"*{suffix}")
    files = sorted(glob.glob(pattern))
    # files = sorted(glob.glob(pattern), key=os.path.getmtime)  # 按照文件修改顺序
    if len(files) > max_files:
        for f in files[:-max_files]:
            try:
                os.remove(f)
                if logger:
                    logger.info(
                        "删除旧日志文件 %s 于 %s",
                        f,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
            except OSError as e:
                if logger:
                    logger.error("删除日志文件 %s 失败: %s", f, e)


def schedule_log_cleanup(
    log_dir: str,
    suffix: str,
    max_files: int,
    logger: Optional[logging.Logger] = None,
) -> None:
    schedule.every().day.at("01:00").do(
        clean_old_logs, log_dir, suffix, max_files, logger
    ).tag("log_cleanup")

    # schedule.every(10).seconds.do(
    #     clean_old_logs, log_dir, suffix, max_files
    # ).tag('log_cleanup')


def rotate_log_file() -> None:
    """Create a new log file when date changes."""
    import config  # late import to avoid circular dependency

    date_str = datetime.now().strftime('%Y%m%d')
    expected = os.path.join(config.LOG_DIR, f"{date_str}heartbeat.log")
    # print(f'date_str:{date_str}, config.LOG_FILE :{config.LOG_FILE } expected:{expected}', )
    if config.LOG_FILE != expected:
        config.logger.removeHandler(config.file_handler)
        config.file_handler.close()
        config.LOG_FILE, config.file_handler = setup_log_file(
            config.LOG_DIR, 'heartbeat.log', config.MAX_LOG_FILES, config.logger
        )
        config.file_handler.setFormatter(config.fmt)
        config.logger.addHandler(config.file_handler)


def schedule_log_rotation() -> None:
    """Schedule daily log rotation."""
    schedule.every().day.at("00:00").do(rotate_log_file).tag("log_rotate")
    # schedule.every(8).seconds.do(rotate_log_file).tag("log_rotate")
