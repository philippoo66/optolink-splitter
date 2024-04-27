import serial
import time

import utils
import optolinkvs2


# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_ringbuffer(buffer, new_bytes):
    for byte in new_bytes:
        buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        buffer.append(byte)  # Füge das neue Byte am Ende hinzu

def log_vito(data, pre, vitolog):
    if(vitolog is not None):
        sd = utils.bbbstr(data)
        vitolog.write(f"{pre}\t{int(time.time()*1000)}\t{sd}\n")


# VS detection ---------------
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
            add_to_ringbuffer(bufferVicon, dataVicon)
            #optolinkvs2_switch.log_vito(dataVicon, "M")  # funktioniert hier nicht!?!?
            log_vito(dataVicon, "M", vitolog_loc)
            fdata = True
            # reset optobuffer
            bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
        if dataOpto:
            serVicon.write(dataOpto)
            add_to_ringbuffer(bufferOpto, dataOpto)
            #optolinkvs2_switch.log_vito(dataOpto, "S")  # funktioniert hier nicht!?!?
            log_vito(dataOpto, "S", vitolog_loc)
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
            return False
                

# viconn request mechanism -------------
vicon_request = bytearray()

def listen_to_Vitoconnect(servicon:serial, vitolog_loc):
    global vicon_request
    while(True):
        succ, _, data = optolinkvs2.receive_vs2telegr(False, True, servicon)
        if(succ == 1):
            vicon_request = data
        elif(data):
            log_vito(data, "X", vitolog_loc)

def get_vicon_request() -> bytearray:
    global vicon_request
    ret = vicon_request
    vicon_request = bytearray()
    return ret

