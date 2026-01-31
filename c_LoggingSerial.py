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

import serial
import time
from c_LoggerUtil import LoggerUtil


class LoggingSerial:
    """
    drop-in Wrapper for serial.Serial
    """

    def __init__(self, *args, **kwargs):
        # --- Logger ----------------------------------------------------
        logger_name = kwargs.pop("logger_name", "serial")
        logger_level = kwargs.pop("logger_level", 20)  # DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50,
        logger_fmt = kwargs.pop("logger_fmt", "%(asctime)s [%(levelname)s]: %(message)s")
        logger_max_bytes = kwargs.pop("logger_max_bytes", 5*1024*1024)  # 10 MB
        logger_backup_count = kwargs.pop("logger_backup_count", 1)
        logger_no_file = kwargs.pop("logger_no_file", False)
        logger_no_console = kwargs.pop("logger_no_console", False)

        loggerutil = LoggerUtil(
            name = logger_name,
            level = logger_level,
            fmt = logger_fmt,
            max_bytes = logger_max_bytes,
            backup_count = logger_backup_count,
            no_file = logger_no_file,
            no_console = logger_no_console,
        )
        #loggerutil.setup_logger()
        self.logger = loggerutil.logger

        # --- echtes Serial-Objekt -------------------------------------
        self._serial = serial.Serial(*args, **kwargs)

        # info
        ts = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        self.logger.info(
            "%s: port=%s baudrate=%s opened",
            ts,
            self._serial.port,
            self._serial.baudrate,
        )

    # -----------------------------------------------------------------
    # Schreiben
    # -----------------------------------------------------------------
    def write(self, data: bytes):
        self.logger.info("tx %s", data.hex())
        return self._serial.write(data)

    # -----------------------------------------------------------------
    # Lesen
    # -----------------------------------------------------------------
    def read(self, size=1) -> bytes:
        data = self._serial.read(size)
        if data:
            self.logger.info("rx %s", data.hex())
        return data

    def read_all(self) -> bytes:
        data = self._serial.read_all()
        if data:
            self.logger.info("rx %s", data.hex())
        return data     # type: ignore

    # -----------------------------------------------------------------
    # Schliessen
    # -----------------------------------------------------------------
    def close(self):
        # try:
            self.logger.info("closing port %s", getattr(self._serial, "port", "(unknown)"))
            self._serial.close()  # echte Serial schließen
        # except Exception:
        #     self.logger.exception("Fehler beim Schließen der seriellen Schnittstelle")

    # -----------------------------------------------------------------
    # Delegation: alles andere wie bei serial.Serial
    # -----------------------------------------------------------------
    def __getattr__(self, name):
        return getattr(self._serial, name)

    # -----------------------------------------------------------------
    # Optional: Context Manager
    # -----------------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.logger.info("exiting LoggingSerial")
        self.close()
