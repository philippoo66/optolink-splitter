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

import serial
import time

import utils
import optolinkvs2
import c_logging


# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_ringbuffer(buffer, new_bytes):
    for byte in new_bytes:
        buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        buffer.append(byte)  # Füge das neue Byte am Ende hinzu


# VS detection ---------------
def detect_vs2(serVicon:serial.Serial, serOpto:serial.Serial, timeout:float) -> bool:
    bufferVicon = bytearray([0xFF, 0xFF, 0xFF])
    bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

    timestart = time.time()

    while True:
        # Lesen von Daten von beiden seriellen Schnittstellen
        dataVicon = serVicon.read()
        dataOpto = serOpto.read()

        # Überprüfen, ob Daten von ser1 empfangen wurden und dann auf ser2 schreiben
        if dataVicon:
            serOpto.write(dataVicon)
            add_to_ringbuffer(bufferVicon, dataVicon)
            c_logging.vitolog.do_log(dataVicon, "M")
            # reset optobuffer
            bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
        if dataOpto:
            serVicon.write(dataOpto)
            add_to_ringbuffer(bufferOpto, dataOpto)
            c_logging.vitolog.do_log(dataOpto, "S")
            # check VS2
            if(bufferVicon == bytearray([0x16, 0x00, 0x00])): 
                if(dataOpto == b'\x06'):
                    # Initialisierungssequenz erkannt und positive Antwort
                    return True
            if(bufferOpto[0] == 0x06): 
                if(bufferOpto[1] == 0x41): 
                    if (bufferOpto[3] == 0x01):
                        # Antwort im VS2 Format erkannt
                        return True
        time.sleep(0.001)
        if(time.time() > timestart + timeout):
            return False
                

# viconn request mechanism -------------
vicon_request = bytearray()

def listen_to_Vitoconnect(servicon:serial):
    global vicon_request
    while(True):
        succ, _, data = optolinkvs2.receive_vs2telegr(False, True, servicon)  # contains sleep(0.005)
        if(succ == 1):
            vicon_request = data
        elif(data):
            c_logging.vitolog.do_log(data, "X")

def get_vicon_request() -> bytearray:
    global vicon_request
    ret = vicon_request
    vicon_request = bytearray()
    return ret

