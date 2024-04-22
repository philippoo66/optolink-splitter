import serial
import time

# VS detection +++++++++++++++++++++++

# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_buffer(buffer, new_bytes):
    for byte in new_bytes:
        buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        buffer.append(byte)  # Füge das neue Byte am Ende hinzu


def detect_vs2(serVicon:serial.Serial, serOpto:serial.Serial, timeout:float) -> bool:
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
            fdata = True
            # reset optobuffer
            bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
        if dataOpto:
            serVicon.write(dataOpto)
            add_to_buffer(bufferOpto, dataOpto)
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
        # if(fdata):
        #     # Zeitstempel in Millisekunden erzeugen
        #     timestamp_ms = int(time.time() * 1000)
        #     # Daten in hexadezimaler Form mit Zeitstempel und Tab getrennt in die Datei schreiben
        #     f.write(f"{timestamp_ms}\t{data1.hex().upper()}\t{data2.hex().upper()}\n")   #\t{bbbstr(ring_buffer)}\n")
        #     #f.flush()  # Puffer leeren, um sicherzustellen, dass die Daten sofort in die Datei geschrieben werden
        time.sleep(0.001)
        if(time.time() > timestart + timeout):
            return False
                
