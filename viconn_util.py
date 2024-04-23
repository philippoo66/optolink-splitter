import serial
import time

import optolinkvs2
from requests_util import bbbstr

# VS detection +++++++++++++++++++++++

# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_buffer(buffer, new_bytes):
    for byte in new_bytes:
        buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        buffer.append(byte)  # Füge das neue Byte am Ende hinzu


def detect_vs2(serVicon:serial.Serial, serOpto:serial.Serial, timeout:float, vitolog_loc) -> bool:
    bufferVicon = bytearray([0xFF, 0xFF, 0xFF])
    bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

    timestart = time.time()

    while True:
        # Lesen von Daten von beiden seriellen Schnittstellen
        dataVicon = serVicon.read()
        dataOpto = serOpto.read()

        fdata = False

        # Überprüfen, ob Daten von ser1 empfangen wurden und dann auf ser2 schreiben
        if dataVicon:
            serOpto.write(dataVicon)
            add_to_buffer(bufferVicon, dataVicon)
            #optolinkvs2_switch.log_vito(dataVicon, "M")  # funktioniert hier nicht!?!?
            if(vitolog_loc is not None):
                vitolog_loc.write(f"M\t{int(time.time()*1000)}\t{bbbstr(dataVicon)}\n")
            fdata = True
            # reset optobuffer
            bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
        if dataOpto:
            serVicon.write(dataOpto)
            add_to_buffer(bufferOpto, dataOpto)
            #optolinkvs2_switch.log_vito(dataOpto, "S")  # funktioniert hier nicht!?!?
            if(vitolog_loc is not None):
                vitolog_loc.write(f"S\t{int(time.time()*1000)}\t{bbbstr(dataOpto)}\n")
            fdata = True
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
            vitolog_loc.close()
            return False
                


vicon_request = bytearray()

def listen_to_Vitoconnect(servicon:serial, vitolog_loc):
    global vicon_request
    while(True):
        succ, _, data = optolinkvs2.receive_vs2telegr(False, True, servicon)
        if(succ == 1):
            vicon_request = data
        elif(data):
            if(vitolog_loc is not None):
                vitolog_loc.write(f"X\t{int(time.time()*1000)}\t{bbbstr(data)}\n")

def get_vicon_request() -> bytearray:
    global vicon_request
    ret = vicon_request
    vicon_request = bytearray()
    return ret

