import logging
import os
from logging.handlers import RotatingFileHandler

# === Logdatei im selben Ordner wie dieses Skript ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "optolinkvs2_switch.log")

# === Logger-Setup =========================================================
def setup_logger(name: str = "optolinkvs2_switch", level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # verhindert doppelte Logs bei root-Logger

    if not logger.handlers:  # nur einmal konfigurieren
        formatter = logging.Formatter(
            #fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            #fmt="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s(): %(message)s",
            fmt="%(asctime)s [%(levelname)s]: %(message)s",
            datefmt="%d.%m.%Y %H:%M:%S"
        )

        # Rotierendes Logfile (max 20 KB, 2 Backups)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=20_000, backupCount=2, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)

        # Konsole
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# === Globale Loggerinstanz ===============================================
logger = setup_logger()
