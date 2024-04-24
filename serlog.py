import serial
import time
from datetime import datetime

# VS detection +++++++++++++++++++++++
ring_buffer = bytearray([0xFF, 0xFF, 0xFF])

# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_buffer(new_bytes):
    global ring_buffer
    for byte in new_bytes:
        ring_buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        ring_buffer.append(byte)  # Füge das neue Byte am Ende hinzu


# utils ++++++++++++++++++++
def bbbstr(data_buffer):
    return ' '.join([format(byte, '02X') for byte in data_buffer])


# main ++++++++++++++++++++++++++++++++
def main():
    # Konfiguration der seriellen Schnittstellen
    # Vitoconnect  (älter: /dev/ttyAMA0)
    #ser1 = serial.Serial('/dev/ttyS0', baudrate=4800, bytesize=8, parity='E', stopbits=2, timeout=0)  # '/dev/ttyS0'
    ser1 = serial.Serial('/dev/ttyS0',
            baudrate=4800,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
            timeout=0)

    # Optolink Kopf
    #ser2 = serial.Serial('/dev/ttyUSB0', baudrate=4800, bytesize=8, parity='E', stopbits=2, timeout=0)  # '/dev/ttyUSB0'
    ser2 = serial.Serial('/dev/ttyUSB0',
            baudrate=4800,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
            timeout=0)

    # VS2 detection
    global ring_buffer
    vs2detectd = False

    now = datetime.now()
    ts = now.strftime("%y%m%d%H%M%S")
    logf = 'serlog_' + ts + '.txt'
    # Öffnen der Ausgabedatei im Schreibmodus
    with open(logf, 'a') as f:
        try:
            while True:
                # Lesen von Daten von beiden seriellen Schnittstellen
                data1 = ser1.read()
                data2 = ser2.read()

                fdata = False

                # Überprüfen, ob Daten von ser1 empfangen wurden und dann auf ser2 schreiben
                if data1:
                    ser2.write(data1)
                    fdata = True
                    if not vs2detectd:
                        add_to_buffer(data1)

                # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
                if data2:
                    ser1.write(data2)
                    fdata = True
                    if not vs2detectd:
                        #print(bbbstr(ring_buffer))
                        if ring_buffer == bytearray([0x16, 0x00, 0x00]): 
                            print("buffer ok")
                            if(data2 == b'\x06'):
                                vs2detectd = True
                                msg = "VS2 Initialisierung erkannt."
                                print(msg)
                                f.write(msg+"\n")
                if fdata:
                    # Zeitstempel in Millisekunden erzeugen
                    timestamp_ms = int(time.time() * 1000)
                    # Daten in hexadezimaler Form mit Zeitstempel und Tab getrennt in die Datei schreiben
                    f.write(f"{timestamp_ms}\t{data1.hex().upper()}\t{data2.hex().upper()}\n")   #\t{bbbstr(ring_buffer)}\n")
                     #f.flush()  # Puffer leeren, um sicherzustellen, dass die Daten sofort in die Datei geschrieben werden

                # Wartezeit für die Schleife, um die CPU-Last zu reduzieren
                time.sleep(0.001)  # Anpassen der Wartezeit je nach Anforderung
        except KeyboardInterrupt:
            print("Abbruch durch Benutzer.")
        finally:
            # Schließen der seriellen Schnittstellen und der Ausgabedatei
            ser1.close()
            ser2.close()

if __name__ == "__main__":
    main()
