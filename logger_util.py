import logging
import os
#import sys
from logging.handlers import RotatingFileHandler

# === Base Dir robust bestimmen ============================================
def get_base_dir():
    # if getattr(sys, "frozen", False):  # PyInstaller-Umgebung
    #     return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
LOG_FILE = os.path.join(BASE_DIR, "optolinkvs2_switch.log")


# === Logger-Setup =========================================================
def setup_logger(
    name: str = "optolinkvs2_switch",
    level=logging.INFO,
    fmt: str = "%(asctime)s [%(levelname)s]: %(message)s",
    datefmt: str = "%d.%m.%Y %H:%M:%S",
    no_file = False,
) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Vorherige Handler entfernen → verhindert doppelte Logs
    logger.handlers.clear()

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if not no_file:
        # Rotierendes Logfile
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=20*1024,   #5 * 1024 * 1024,   # 5 MB
            backupCount=1,      #3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Konsole
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# === Globale Loggerinstanz ===============================================
no_file = False
try:
    import settings_ini
    no_file = settings_ini.no_logger_file
except:
    pass 
logger = setup_logger(no_file=no_file)
