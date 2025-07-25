import logging
import pythoncom
import wmi

logger = logging.getLogger(__name__)


def get_cpu_serial():
    """通过 WMI 获取 CPU 序列号"""
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        pid = c.Win32_Processor()[0].ProcessorId.strip()
        logger.info(f'通过 WMI 获取 CPU 序列：{pid}')
        return pid
    except Exception as e:
        logger.error(f'WMI 获取 CPU 序列失败：{e}')
        raise RuntimeError('无法获取真实的 CPU 序列，请确认运行环境允许 WMI 调用。')