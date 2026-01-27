import serial

import optolinkvs2
import optolinkvs1
import viconn_util
from c_settings_adapter import settings


VS2 = not settings.vs1protocol


def init_protocol(ser:serial.Serial) -> bool:
    if(VS2):
        return optolinkvs2.init_vs2(ser)
    else:
        return optolinkvs1.init_protocol(ser)


def read_datapoint_ext(addr:int, rdlen:int, ser:serial.Serial) -> tuple[int, int, bytearray]: 
    if(VS2):
        return optolinkvs2.read_datapoint_ext(addr, rdlen, ser)
    else:
        return optolinkvs1.read_datapoint_ext(addr, rdlen, ser)


def write_datapoint_ext(addr:int, data:bytes, ser:serial.Serial) -> tuple[int, int, bytearray]:
    if(VS2):
        return optolinkvs2.write_datapoint_ext(addr, data, ser)
    else:
        return optolinkvs1.write_datapoint_ext(addr, data, ser)


def do_request(ser:serial.Serial, fctcode:int, addr:int, rlen:int, data:bytes=b'', protid=0x00) -> tuple[int, int, bytearray]:
    if(VS2):
        return optolinkvs2.do_request(ser, fctcode, addr, rlen, data, protid)
    else:
        #return 0xAF, addr, bytearray()
        raise NotImplementedError("request command not supported with VS1/KW, use raw instead")


def receive_telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None, mqtt_publ_callback=None) -> tuple[int, int, bytearray]:       # type: ignore
    """
    Empfaengt ein Optolink-Telegramm als Antwort auf ein Optolink Request.

    Parameter:
    ----------
    resptelegr : bool
        Wenn True, wird das empfangene Telegramm als Antworttelegramm interpretiert.
        Wenn False, wird ein Master Request Telegramm erwartet.
    raw : bool
        Gibt an, ob der Empfangsmodus roh (unverarbeitet) ist.
        True = Rohdatenmodus (keine Protokollauswertung),
        False = dekodierte Protokolldaten.
    ser : serial.Serial
        Geoeffnete serielle Schnittstelle (z. B. COM-Port), ueber die das Telegramm empfangen wird.
    ser2 : serial.Serial, optional
        Zweite serielle Schnittstelle (z. B. bei Weiterleitung oder Duplexbetrieb).
        Standardwert ist None.
    mqtt_publ_callback :
        Funktion zum Publizieren der (Vitoconnect) Daten auf MQTT

    Rueckgabewerte:
    ---------------
    tuple[int, int, bytearray]
        Enthaelt folgende Elemente:

        1. **ReturnCode (int)**  
           Statuscode des Empfangs:  
           - 0x01 = Erfolg  
           - 0x03 = Fehlermeldung  
           - 0x15 = NACK  
           - 0x20 = Byte0-unbekannt-Fehler 
           - 0x41 = STX-Fehler  
           - 0xAA = Handle verloren  
           - 0xFD = Paketlaengenfehler  
           - 0xFE = CRC-Fehler  
           - 0xFF = Timeout  

        2. **Addr (int)**  
           Adresse des Datenpunktes.

        3. **Data (bytearray)**  
           Nutzdaten des empfangenen Telegramms.

    Hinweise:
    ----------
    Diese Funktion blockiert, bis das Telegramm vollstaendig empfangen oder ein Timeout erreicht wurde.
    """
    if(VS2):
        return optolinkvs2.receive_telegr(resptelegr, raw, ser, ser2, mqtt_publ_callback)
    else:
        return optolinkvs1.receive_telegr(resptelegr, raw, ser, ser2)


def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, bytearray]:        # type: ignore
    # same everywhere, only one to service
    return optolinkvs2.receive_fullraw(eot_time, timeout, ser, ser2) 
    # if(VS2):
    #     return optolinkvs2.receive_fullraw(eot_time, timeout, ser, ser2) #, mqtt_publ_callback)
    # else:
    #     return optolinkvs1.receive_fullraw(eot_time, timeout, ser, ser2)

def reset_vs1sync():
    optolinkvs1.reset_sync()


def wait_for_vicon(serVicon:serial.Serial, serOpto:serial.Serial, timeout:float) -> bool:
    if(VS2):
        return viconn_util.detect_vs2(serVicon, serOpto, timeout)
    else:
        return viconn_util.detect_vs1(serVicon, serOpto, timeout)

