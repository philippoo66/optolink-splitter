'''
   Copyright 2026 philippoo66
   
   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import logging
import os
from logging.handlers import RotatingFileHandler


class LoggerUtil:
    # === Base Dir robust bestimmen ======================================
    @staticmethod
    def get_base_dir():
        # if getattr(sys, "frozen", False):  # PyInstaller-Umgebung
        #     return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    # === Initialisierung ================================================
    def __init__(
            self,
            name: str = "loggerutil",
            # == level constants: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50,
            level = logging.INFO,
            # == fmt examples: ===========================
            # "%(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s"    mit Millisekunden
            # "%(created).3f [%(levelname)s]: %(message)s"              Unix-Zeitstempel in Sekunden (float)
            # "%(relativeCreated)d [%(levelname)s]: %(message)s"        Millisekunden seit Start des Logging-Systems
            fmt: str = "%(asctime)s [%(levelname)s]: %(message)s",
            datefmt: str = "%Y-%m-%d %H:%M:%S",
            no_console: bool = False,
            no_file: bool = False,
            log_file: str = "",
            max_bytes: int = 5 * 1024 * 1024,  # 5 MB
            backup_count: int = 1,
        ):

        self.name = name

        self.logger = logging.getLogger(self.name)       
        self.logger.setLevel(level)
        self.logger.propagate = False
        self.logger.handlers.clear() # doppelte Handler vermeiden

        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

        if not no_file:
            base_dir = self.get_base_dir()
            self.log_file = log_file or os.path.join(base_dir, f"{name}.log")

            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if not no_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
