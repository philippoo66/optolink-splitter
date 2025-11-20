import socket

from logger_util import logger

#logger = logging.getLogger(__name__)
#logger = logging.getLogger("tcptest.txt")

class TcpServer:
    def __init__(self, host: str, port: int, verbose: bool = False):
        self.host = host
        self.port = port
        self.verbose = verbose

        self.server_socket = None
        self.client_socket = None
        self.client_address = None

        self.received_data = ""
        self.exit_flag = False

    # ---------------------------------------------------------
    # Startet den Server, wartet auf Verbindung (BLOCKIEREND)
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

        # BLOCKIEREND warten auf Client
        self.client_socket, self.client_address = self.server_socket.accept()
        logger.info(f"TCP Connection from {self.client_address}")
        #print(f"TCP Connection from {self.client_address}")

        # Server-Socket nicht mehr nötig
        self.server_socket.close()
        self.server_socket = None

        # BLOCKIEREND empfangen, bis exit oder FIN
        self._listen_blocking()

        # Nach Empfang -> alles schließen
        self.stop()

    # ---------------------------------------------------------
    # BLOCKIERENDES Empfangen (Endlosschleife)
    # ---------------------------------------------------------
    def _listen_blocking(self):
        #logger.info("enter TCP listen loop")
        #print("enter TCP listen loop")

        while not self.exit_flag:
            try:
                data = self.client_socket.recv(1024)

                # FIN-Flag -> Verbindung weg
                if not data:
                    logger.info("TCP Connection ended (FIN)")
                    #print("TCP Connection lost (FIN)")
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

                    if m == "exit":
                        logger.info("TCP exit command received")
                        #print("TCP exit command received")
                        break

                    elif m == "flushcsv":
                        import viessdata_util
                        viessdata_util.buffer_csv_line([], True)

                    else:
                        self.received_data = msg
                        #temp
                        #self.send(f"received: {msg}")

            except ConnectionError:
                logger.warning("TCP Connection lost")
                #print("TCP Connection lost")
                break
            except Exception as e:
                logger.error(e)
                #print(f"ERROR: {e}")
                break

    # ---------------------------------------------------------
    # Sendet Antwort an den Client
    # ---------------------------------------------------------
    def send(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        try:
            self.client_socket.send(data)
            if self.verbose:
                print("TCP sent:", data)
        except:
            pass

    # ---------------------------------------------------------
    # Holt gespeicherte Nachricht
    # ---------------------------------------------------------
    def get_request(self) -> str:
        msg = self.received_data
        self.received_data = ""
        return msg

    # ---------------------------------------------------------
    # Schließt alles
    # ---------------------------------------------------------
    def stop(self):
        logger.info("closing TCP Server")
        #print("Stopping TCP Server")

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

    server = None  # global für Cleanup

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

        # Optional: warte kurz, damit Threads sauber schließen
        time.sleep(0.5)

        print("Programm beendet.")
    
    finally:
        print("exit script")



if __name__ == "__main__":
    main()
