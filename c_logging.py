'''
   Copyright 2025 philippoo66
   
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

import time
import utils

class cLogging:
    def __init__(self, log_file="app.log"):
        """
        Initialisiert die cLogging-Klasse mit einem Logdateinamen.
        """
        self.log_file = log_file
        self.log_handle = None

    def open_log(self):
        """
        Öffnet die Logdatei im Anhängemodus.
        """
        try:
            self.log_handle = open(self.log_file, 'a')
            self.do_log("Log file opened.")
        except Exception as e:
            print(f"Error opening log file: {e}")

    def close_log(self):
        """
        Schließt die Logdatei.
        """
        if self.log_handle:
            self.do_log("Log file closed.")
            self.log_handle.close()
            self.log_handle = None

    def do_log(self, data, pre="i"):
        """
        Schreibt einen Logeintrag in die Logdatei mit Zeitstempel.
        """
        if self.log_handle:
            # timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # log_entry = f"[{timestamp}] {message}\n"
            # self.log_handle.write(log_entry)
            if(isinstance(data,str)):
                sd = data
            else:
                sd = utils.bbbstr(data)
            self.log_handle.write(f"{pre}\t{int(time.time()*1000)}\t{sd}\n")
        # else:
        #     print("Log file is not open. Cannot write log entry.")

    def __del__(self):
        """
        Sicherstellen, dass die Logdatei geschlossen wird, wenn die Instanz zerstört wird.
        """
        self.close_log()


# for global use
vitolog = cLogging('vitolog.txt')




# Beispielverwendung
if __name__ == "__main__":
    logger = cLogging("my_app.log")
    logger.open_log()
    logger.do_log("This is a test log entry.")
    logger.close_log()