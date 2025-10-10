'''
   Copyright 2024 philippoo66
   
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

import threading
import socket
import time

import viessdata_util
from logger_util import logger


tcp_client = socket.socket()  #None  # None, bis der Client-Socket erstellt wird
recdata = bytes()
exit_flag = False

fverbose = True


def run_tcpip(host, port) -> socket:
    global exit_flag
    global fverbose
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the address and port
    server_socket.bind((host, port))
    # Listen for incoming connections
    if(not exit_flag):
        logger.info(f"TCP Server listening on {host}:{port}")  #if(fverbose): 
        server_socket.listen(1)
        # Wait for a connection
        client_socket, client_address = server_socket.accept()
        logger.info(f"TCP Connection from {client_address}")  #if(fverbose): 
        # Schließe den Server-Socket, da er nicht mehr benötigt wird
        server_socket.close()
        return client_socket
        

def listen_tcpip(client:socket):
    global exit_flag
    global fverbose
    global recdata

    logger.info("enter listen loop")
    while(not exit_flag):
        try:
            data = client.recv(1024)
            if data:
                if(fverbose): print("TCP recd:", data)  #bbbstr(data)
                msg = data.decode('utf-8').replace(' ','').replace('\0','').replace('\n','').replace('\r','').replace('"','').replace("'","")
                if(msg):
                    m = msg.lower() 
                    if(m == "exit"):
                        logger.info("TCP Connection exit")
                        time.sleep(0.5)
                        break
                    elif(m == "flushcsv"):
                        viessdata_util.buffer_csv_line([], True)
                    else:
                        recdata = msg
        except ConnectionError:
            logger.warning("TCP Connection lost")
            break
        except Exception as e:
            logger.error(e)


def tcpip4ever(port:int, verbose = True):
    global exit_flag
    global tcp_client
    global fverbose
    # apply verbose flag
    fverbose = verbose
    # loop buiding connection (if lost) and receiving
    while(not exit_flag):
        tcp_client.close()
        tcp_client = run_tcpip('0.0.0.0', port)
        listen_tcpip(tcp_client) 
    # Schließe den Client-Socket, wenn der Hauptthread beendet wird
    if tcp_client:
        tcp_client.close()


def get_tcp_request() -> str:
    global recdata
    ret = recdata
    # clear receive buffer
    recdata = ''
    return ret

def send_tcpip(data):
    global tcp_client
    global fverbose
    # if is string make bytes 
    if(isinstance(data, str)):
        data = bytes(data, 'utf-8')
    # send out
    tcp_client.send(data)
    if(fverbose): print("TCP sent:", data)
    

def exit_tcpip():
    logger.info("exiting TCP/IP client")
    global exit_flag
    exit_flag = True


# ------------------------
# main for test only
# ------------------------
def main():
    global exit_flag

    tcp_thread = threading.Thread(target=tcpip4ever, args=(65234,True))
    tcp_thread.daemon = True  # Setze den Thread als Hintergrundthread. WICHTIG für Ctrl+C etc!
    tcp_thread.start()

    try:
        while(not exit_flag):
            mydata = get_tcp_request()
            print("###", mydata)
            if(mydata):
                send_tcpip("received: " + mydata)  #.decode('utf-8'))
            time.sleep(0.5)
    except Exception as e:
        print("main", e)
        exit_flag = True

    tcp_thread.join()


if __name__ == "__main__":
    main()
