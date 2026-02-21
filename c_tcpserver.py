import socket

from logger_util import logger

#logger = logging.getLogger(__name__)
#logger = logging.getLogger("tcptest.txt")

class TcpServer:
    def __init__(self, host: str, port: int, verbose: bool = False):
        self.host = host
        self.port = port
        self.verbose = verbose
        # callback for 'special' commands
        self.command_callback = None  

        self.server_socket = None
        self.client_socket = None
        self.client_address = None

        self.received_data = ""
        self.exit_flag = False

    # ---------------------------------------------------------
    # Startet den Server
    # ---------------------------------------------------------
    def run(self):
        self.exit_flag = False
        self.received_data = ""

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Sofortige Port-Wiederverwendung
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Binden + Listen
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        logger.info(f"TCP Server listening on {self.host}:{self.port}")
        #print(f"TCP Server listening on {self.host}:{self.port}")

        # warten auf Client
        self._wait_for_client()

        if not self.server_socket: return

        # Server-Socket nicht mehr noetig
        self.server_socket.close()
        self.server_socket = None

        # empfangen, bis exit oder FIN
        self._listen()

        # Nach Empfang -> alles schliessen
        self.stop()

    
    # ---------------------------------------------------------
    # auf Verbindung warten (Endlosschleife)
    # ---------------------------------------------------------
    def _wait_for_client(self):
        if not self.server_socket or self.exit_flag:
            return
        
        self.server_socket.settimeout(0.5)   # akzeptiere max 0.5s blockierend

        while self.server_socket and not self.exit_flag:
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                logger.info(f"TCP Connection from {self.client_address}")
                break
            except socket.timeout:
                continue   # pruefe exit_flag, weiter warten
            except OSError as e:
                # falls socket von aussen closed wurde -> abbrechen
                logger.info(f"accept() aborted: {e}")
                break

    # ---------------------------------------------------------
    # Empfangen (Endlosschleife)
    # ---------------------------------------------------------
    def _listen(self):
        if not self.client_socket or self.exit_flag:
            return
        
        self.client_socket.settimeout(0.5)

        while self.client_socket and not self.exit_flag:
            try:
                data = self.client_socket.recv(1024)

                if not data:
                    logger.info("TCP Connection ended (FIN)")
                    break

                if self.verbose:
                    print("TCP recd:", data)

                msg = (
                    data.decode("utf-8")
                    .strip()
                    .replace("\0", "")
                    .replace("\r", "")
                    .replace("\n", "")
                    .replace('"', "")
                    .replace("'", "")
                )

                if msg:
                    m = msg.lower()
                    # if m == "exit":
                    #     logger.info("TCP exit command received")
                    #     break
                    # elif m == "flushcsv":
                    #     import viessdata_util
                    #     viessdata_util.buffer_csv_line([], True)
                    if(self.command_callback) and self.command_callback(m,2):
                        pass
                    else:
                        self.received_data = msg

            except socket.timeout:
                # keine Daten → einfach exit_flag erneut pruefen
                continue

            except ConnectionError:
                logger.warning("TCP Connection lost")
                break

            except Exception:
                logger.exception("_listen")
                break

    # ---------------------------------------------------------
    # Sendet Antwort an den Client
    # ---------------------------------------------------------
    def send(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8") + b"\n"

        try:
            self.client_socket.send(data)
            if self.verbose:
                print("TCP sent:", data)
        except Exception as e:
            logger.warning(f"TCP send failed: {e}, data: {data}")

    # ---------------------------------------------------------
    # Holt gespeicherte Nachricht
    # ---------------------------------------------------------
    def get_request(self) -> str:
        msg = self.received_data
        self.received_data = ""
        return msg

    # ---------------------------------------------------------
    # Schliesst alles
    # ---------------------------------------------------------
    def stop(self):
        if self.exit_flag: 
            return

        logger.info("closing TCP Server")

        self.exit_flag = True

        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass
        self.client_socket = None

        try:
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        self.server_socket = None



# ------------------------
# main for test only
# ------------------------
import threading
import time

def main():
    print("Starte TCP-Server-Endlosschleife. STRG+C zum Beenden.")

    server = None  # global fuer Cleanup

    def tcp_loop():

        while True:
            server = TcpServer("0.0.0.0", 9000, verbose=True)

            # # Server in Thread starten
            # t = threading.Thread(target=server.start, daemon=True)
            # t.start()

            # # # Warten bis der Thread fertig ist, aber STRG+C abfangen
            # # while t.is_alive():
            # #     t.join(timeout=0.5)  # kurz timeout, damit KeyboardInterrupt reagiert
            # t.join()
            server.run()

            print("TCP-Session beendet. Warte 1 Sekunde, dann starte ich neu...\n")
            time.sleep(1)

    try:
        t = threading.Thread(target=tcp_loop, daemon=True)
        t.start()
        t.join()

    except KeyboardInterrupt:
        print("\nSTRG+C erkannt. Beende alles...")

        if server:
            server.stop()

        # Optional: warte kurz, damit Threads sauber schliessen
        time.sleep(0.5)

        print("Programm beendet.")
    
    finally:
        print("exit script")



if __name__ == "__main__":
    main()
