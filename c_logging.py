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
            self.do_log([], "Log file opened.")
        except Exception as e:
            print(f"Error opening log file: {e}")

    def close_log(self):
        """
        Schließt die Logdatei.
        """
        if self.log_handle:
            self.do_log([], "Log file closed.")
            self.log_handle.close()
            self.log_handle = None

    def do_log(self, data, pre):
        """
        Schreibt einen Logeintrag in die Logdatei mit Zeitstempel.
        """
        if self.log_handle:
            # timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # log_entry = f"[{timestamp}] {message}\n"
            # self.log_handle.write(log_entry)
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
    logger.do_log([], "This is a test log entry.")
    logger.close_log()