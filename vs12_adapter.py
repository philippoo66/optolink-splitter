import serial

import optolinkvs2
import optolinkvs1
import viconn_util
import settings_ini


def init_protocol(ser:serial.Serial) -> bool:
    if(not settings_ini.vs1protocol):
        return optolinkvs2.init_vs2(ser)
    else:
        return optolinkvs1.init_protocol(ser)


def read_datapoint_ext(addr:int, rdlen:int, ser:serial.Serial) -> tuple[int, int, bytearray]: 
    if(not settings_ini.vs1protocol):
        return optolinkvs2.read_datapoint_ext(addr, rdlen, ser)
    else:
        return optolinkvs1.read_datapoint_ext(addr, rdlen, ser)


def write_datapoint_ext(addr:int, data:bytes, ser:serial.Serial) -> tuple[int, int, bytearray]:
    if(not settings_ini.vs1protocol):
        return optolinkvs2.write_datapoint_ext(addr, data, ser)
    else:
        return optolinkvs1.write_datapoint_ext(addr, data, ser)


def receive_telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None, mqtt_publ_callback=None) -> tuple[int, int, bytearray]:
    """
    Empfängt ein VS2-Telegramm als Antwort auf eine Virtual_READ oder Virtual_WRITE-Anfrage.

    Parameter:
    ----------
    resptelegr : bool
        Wenn True, wird das empfangene Telegramm als Antworttelegramm interpretiert.
        Wenn False, wird ein reguläres Datentelegramm erwartet.
    raw : bool
        Gibt an, ob der Empfangsmodus roh (unverarbeitet) ist.
        True = Rohdatenmodus (keine Protokollauswertung),
        False = dekodierte Protokolldaten.
    ser : serial.Serial
        Geöffnete serielle Schnittstelle (z. B. COM-Port), über die das Telegramm empfangen wird.
    ser2 : serial.Serial, optional
        Zweite serielle Schnittstelle (z. B. bei Weiterleitung oder Duplexbetrieb).
        Standardwert ist None.
    mqtt_publ_callback :
        Funktion zum Publizieren der (Vitoconnect) Daten auf MQTT

    Rückgabewerte:
    ---------------
    tuple[int, int, bytearray, int, int, int]
        Enthält folgende Elemente:

        1. **ReturnCode (int)**  
           Statuscode des Empfangs:  
           - 0x01 = Erfolg  
           - 0x03 = Fehlermeldung  
           - 0x15 = NACK  
           - 0x20 = Unbekannter B0-Fehler  
           - 0x41 = STX-Fehler  
           - 0xAA = Handle verloren  
           - 0xFD = Paketlängenfehler  
           - 0xFE = CRC-Fehler  
           - 0xFF = Timeout  

        2. **Addr (int)**  
           Adresse des Zielgeräts.

        3. **Data (bytearray)**  
           Nutzdaten des empfangenen Telegramms.

    Hinweise:
    ----------
    Diese Funktion blockiert, bis das Telegramm vollständig empfangen oder ein Timeout erreicht wurde.
    """
    if(not settings_ini.vs1protocol):
        return optolinkvs2.receive_telegr(resptelegr, raw, ser, ser2, mqtt_publ_callback)
    else:
        return optolinkvs1.receive_telegr(resptelegr, raw, ser, ser2)


def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, bytearray]:
    # same everywhere, only one to service
    return optolinkvs2.receive_fullraw(eot_time, timeout, ser, ser2) 
    # if(not settings_ini.vs1protocol):
    #     return optolinkvs2.receive_fullraw(eot_time, timeout, ser, ser2) #, mqtt_publ_callback)
    # else:
    #     return optolinkvs1.receive_fullraw(eot_time, timeout, ser, ser2)

def reset_vs1sync():
    optolinkvs1.reset_sync()


def wait_for_vicon(serVicon:serial.Serial, serOpto:serial.Serial, timeout:float) -> bool:
    if(not settings_ini.vs1protocol):
        return viconn_util.detect_vs2(serVicon, serOpto, timeout)
    else:
        return viconn_util.detect_vs1(serVicon, serOpto, timeout)
