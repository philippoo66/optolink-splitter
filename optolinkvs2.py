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
import sys
import time

from c_settings_adapter import settings
from logger_util import logger
import utils


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Optolink VS2 / 300 Protocol, mainly virtual r/w datapoints
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def init_vs2(ser:serial.Serial) -> bool:

    # after the serial port read buffer is emptied
    ser.reset_input_buffer()

    # then an EOT (0x04) is send
    ser.write(bytes([0x04]))

    # and for 30x100ms waited for an ENQ (0x05)
    i = 0
    while(i < 30):
        time.sleep(0.1)
        buff = ser.read(1)
        if(settings.show_opto_rx):
            print(buff)
        if(len(buff) > 0):
            if(int(buff[0]) == 0x05):
                break
        i+=1

    if(i == 30):
        logger.error("init_vs2: Timeout waiting for 0x05")
        return False
    
    ser.reset_input_buffer()

    # after which a VS2_START_VS2, 0, 0 (0x16,0x00,0x00) is send
    ser.write(bytes([0x16,0x00,0x00]))

    # and within 30x100ms an VS2_ACK (0x06) is expected.
    i = 0
    while(i < 30):
        time.sleep(0.1)
        buff = ser.read(1)
        if(settings.show_opto_rx):
            print(buff)
        if(len(buff) > 0):
            if(int(buff[0]) == 0x06):
                break
        i+=1

    if(i == 30):
        logger.error("init_vs2: Timeout waiting for 0x06")
        return False

    return True


def read_datapoint(addr:int, rdlen:int, ser:serial.Serial) -> bytes:
    _,_,data = read_datapoint_ext(addr, rdlen, ser)
    return data

def read_datapoint_ext(addr:int, rdlen:int, ser:serial.Serial) -> tuple[int, int, bytearray]: 
    outbuff = bytearray(8)
    outbuff[0] = 0x41   # 0x41 Telegrammstart
    outbuff[1] = 0x05   # Len Payload, hier immer 5
    outbuff[2] = 0x00   # 0x00 Request Message
    outbuff[3] = 0x01   # 0x01 Virtual_READ
    outbuff[4] = (addr >> 8) & 0xFF  # hi byte
    outbuff[5] = addr & 0xFF         # lo byte
    outbuff[6] = rdlen   # Anzahl der zu lesenden Daten-Bytes
    outbuff[7] = calc_crc(outbuff)

    ser.reset_input_buffer()
    # After message is send, 
    ser.write(outbuff)
    #print("R tx", utils.bbbstr(outbuff))

    # return retcode, addr, data
    return receive_telegr(True, False, ser)


def write_datapoint(addr:int, data:bytes, ser:serial.Serial) -> bool:
    retcode,_,_ = write_datapoint_ext(addr, data, ser)
    return (retcode == 0x01)

def write_datapoint_ext(addr:int, data:bytes, ser:serial.Serial) -> tuple[int, int, bytearray]:
    wrlen = len(data)
    outbuff = bytearray(wrlen+8)
    outbuff[0] = 0x41   # 0x41 Telegrammstart
    outbuff[1] = 5 + wrlen  # Len Payload
    outbuff[2] = 0x00   # 0x00 Request Message
    outbuff[3] = 0x02   # 0x02 Virtual_WRITE 
    outbuff[4] = (addr >> 8) & 0xFF  # hi byte
    outbuff[5] = addr & 0xFF         # lo byte
    outbuff[6] = wrlen  # Anzahl der zu schreibenden Daten-Bytes
    for i in range(int(wrlen)):
        outbuff[7 + i] = data[i]
    outbuff[7 + wrlen] = calc_crc(outbuff)

    ser.reset_input_buffer()
    ser.write(outbuff)
    #print("W tx", utils.bbbstr(outbuff))

    # return retcode, addr, data
    return receive_telegr(True, False, ser)


def do_request(ser:serial.Serial, fctcode:int, addr:int, rlen:int, data:bytes=b'', protid=0x00) -> tuple[int, int, bytearray]:
    pldlen = 5 + len(data)
    outbuff = bytearray(pldlen + 3)  # + STX, LEN, CRC
    outbuff[0] = 0x41                # 0x41 Telegrammstart
    outbuff[1] = pldlen              # Len Payload
    outbuff[2] = protid              # Protocol|MsgIdentifier
    outbuff[3] = fctcode & 0xFF      # function code (sequ num wird hier unterdrueckt/ignoriert/ueberschrieben)
    outbuff[4] = (addr >> 8) & 0xFF  # hi byte
    outbuff[5] = addr & 0xFF         # lo byte
    outbuff[6] = rlen                # Anzahl requested Data-Bytes oder data len
    for i in range(len(data)):
        outbuff[7 + i] = data[i]
    outbuff[-1] = calc_crc(outbuff)

    print(utils.bbbstr(outbuff))

    ser.reset_input_buffer()
    ser.write(outbuff)
    #print("W tx", utils.bbbstr(outbuff))

    # return retcode, addr, data
    return receive_telegr(True, False, ser)


def receive_telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None, mqtt_publ_callback=None) -> tuple[int, int, bytearray]:       # type: ignore
    """
    Empfaengt ein VS2-Telegramm als Antwort auf eine Virtual_READ oder Virtual_WRITE-Anfrage.

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
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, 03=ErrMsg, 15=NACK, 20=UnknB0_Err, 41=STX_Err, AA=HandleLost, FD=PlLen_Err, FE=CRC_Err, FF=TimeOut (all hex)
    # receives the V2 response to a Virtual_READ or Virtual_WRITE request
    state = 0
    inbuff = bytearray()
    alldata = bytearray()
    retdata = bytearray()
    addr = 0
    msgid = 0x100  # message type identifier, byte 2 (3. byte; 0 = Request Message, 1 = Response Message, 2 = UNACKD Message, 3 = Error Message) 
    msqn = 0x100   # message sequence number, top 3 bits of byte 3
    fctcd = 0x100  # function code, low 5 bis of byte 3 (https://github.com/sarnau/InsideViessmannVitosoft/blob/main/VitosoftCommunication.md#defined-commandsfunction-codes)
    dlen = -1

    # for up 30x100ms serial data is read. (we do 600x5ms)
    for _ in range(600):
        time.sleep(0.005)
        try:
            inbytes = ser.read_all()
            if(inbytes):
                inbuff += inbytes
                alldata += inbytes
        except:
            utils.comm_error(True)
            return 0xAA, 0, retdata

        # ggf. gleich durchleiten 
        if(ser2 is not None):
            if(inbytes):
                ser2.write(inbytes)
        
        # evaluate
        if(state == 0):
            if(resptelegr):
                if(len(inbuff) > 0):
                    if(settings.show_opto_rx):
                        print("rx", format(inbuff[0], settings.data_hex_format))
                    if(inbuff[0] == 0x06): # VS2_ACK
                        state = 1
                    elif(inbuff[0] == 0x15): # VS2_NACK
                        logger.error("VS2 NACK Error")
                        retdata = alldata
                        if(mqtt_publ_callback):
                            mqtt_publ_callback(0x15, addr, retdata, msgid, msqn, fctcd, dlen)
                        utils.comm_error(True)
                        return 0x15, 0, retdata       # hier muesste ggf noch ein eventueller Rest des Telegrams abgewartet werden 
                    else:
                        logger.error(f"VS2 unknown first byte Error, {inbuff[0]:02X}")
                        retdata = alldata
                        if(mqtt_publ_callback):
                            mqtt_publ_callback(0x20, addr, retdata, msgid, msqn, fctcd, dlen)
                        utils.comm_error(True)
                        return 0x20, 0, retdata
                    # erstes Byte abtrennen
                    inbuff = inbuff[1:]
            else:
                state = 1
        
        # ab hier Master Request und Slave Response identischer Aufbau (abgesehen von Error Message und sowas)
        if(state == 1):
            if(len(inbuff) > 0):
                if(inbuff[0] != 0x41): # STX
                    logger.error(f"VS2 STX Error, {inbuff[0]:02X}")
                    retdata = alldata
                    if(mqtt_publ_callback):
                        mqtt_publ_callback(0x41, addr, retdata, msgid, msqn, fctcd, dlen)
                    #if(raw): retdata = alldata
                    utils.comm_error(True)
                    return 0x41, 0, retdata  # hier muesste ggf noch ein eventueller Rest des Telegrams abgewartet werden
                state = 2

        if(state == 2):
            if(len(inbuff) > 1):  # STX, Len
                pllen = inbuff[1]
                if(pllen < 5):  # protocol_Id + MsgId|FnctCode + AddrHi + AddrLo + BlkLen
                    print("rx", utils.bbbstr(inbuff))
                    logger.error(f"VS2 Len Error, {pllen}")
                    retdata = alldata
                    if(mqtt_publ_callback):
                        mqtt_publ_callback(0xFD, addr, retdata, msgid, msqn, fctcd, dlen)
                    #if(raw): retdata = alldata
                    utils.comm_error(True)
                    return 0xFD, 0, retdata  # alldata?!
                if(len(inbuff) >= pllen + 3):  # STX + Len + Payload + CRC
                    # receive complete
                    if(settings.show_opto_rx):
                        print("rx", utils.bbbstr(inbuff))
                    inbuff = inbuff[:pllen+4]  # make sure no tailing trash 
                    msgid = inbuff[2]
                    msqn = (inbuff[3] & 0xE0) >> 5
                    fctcd = inbuff[3] & 0x1F
                    addr = (inbuff[4] << 8) + inbuff[5]  # may be bullshit in case of raw
                    dlen = inbuff[6]
                    retdata = inbuff[7:pllen+2]   # STX + Len + ProtId + MsgId|FnctCode + AddrHi + AddrLo + BlkLen (+ Data) + CRC
                    crc = calc_crc(inbuff)
                    if(inbuff[-1] != crc):
                        logger.error(f"VS2 CRC Error, {inbuff[-1]:02X}/{crc:02X}")
                        if(mqtt_publ_callback):
                            mqtt_publ_callback(0xFE, addr, retdata, msgid, msqn, fctcd, dlen)
                        if(raw): retdata = alldata
                        utils.comm_error(True)
                        return 0xFE, addr, retdata
                    if(inbuff[2] & 0x0F == 0x03):
                        #logger.info(f"Error Message {utils.bbbstr(retdata)} on 0x{addr:04x}")
                        if(mqtt_publ_callback):
                            mqtt_publ_callback(0x03, addr, retdata, msgid, msqn, fctcd, dlen)
                        if(raw): retdata = alldata
                        utils.comm_error(False)
                        return 0x03, addr, retdata
                    #success
                    if(mqtt_publ_callback):
                        mqtt_publ_callback(0x01, addr, retdata, msgid, msqn, fctcd, dlen)
                    if(raw): retdata = alldata
                    utils.comm_error(False)
                    return 0x01, addr, retdata
    # timout if get to here
    if(settings.show_opto_rx):
        logger.warning("rx telegr timeout")
    if(mqtt_publ_callback):
        mqtt_publ_callback(0xFF, addr, retdata, msgid, msqn, fctcd, dlen)
    if(raw): retdata = alldata
    utils.comm_error(True)
    return 0xFF, addr, retdata


def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, bytearray]:        # type: ignore
    # times in seconds
    inbuff = b''
    start_time = time.monotonic()
    last_receive_time = start_time

    while True:
        time.sleep(0.005)
        # Zeichen vom Serial Port lesen
        inbytes = ser.read_all()

        if inbytes:
            # Daten zum Datenpuffer hinzufuegen
            inbuff += inbytes
            last_receive_time = time.monotonic()
            if(ser2 is not None):
                ser2.write(inbytes)
        elif inbuff and (time.monotonic() > last_receive_time + eot_time):
            # if data received and no further receive since more than eot_time
            if(settings.show_opto_rx):
                print("rx", utils.bbbstr(inbuff))
            utils.comm_error(False)
            return 0x01, bytearray(inbuff)

        if(time.monotonic() > start_time + timeout):
            if(settings.show_opto_rx):
                print("rx fullraw timeout", utils.bbbstr(inbuff))
            utils.comm_error(True)
            return 0xFF, bytearray(inbuff)


def calc_crc(telegram) -> int:
    # CRC, a modulo-256 addition of bytes from Block Length and the additional bytes.
    firstbyte = 1  # ignore leading STX 0x41
    lastbyte = telegram[1] + 1  # len payload + len byte itself
    return sum(telegram[firstbyte:lastbyte+1]) % 0x100





# --------------------
# main for test only
# --------------------
def main():
    port = "COM4"  #'/dev/ttyUSB0' #'COM1'

    if(len(sys.argv) > 1):
        port = sys.argv[1]

    # Serielle Port-Einstellungen
    ser = serial.Serial(port, baudrate=4800, bytesize=8, parity='E', stopbits=2, timeout=0) 

    try:
        # Serial Port oeffnen
        if not ser.is_open:
            ser.open()

        if not init_vs2(ser):
            raise Exception("init_vs2 failed.")
        
        # read test
        if(True):
            while(True):
                buff = read_datapoint(0x00f8, 8, ser)
                print("0x00f8", utils.bbbstr(buff))
                time.sleep(0.1)

                buff = read_datapoint(0x0802, 2, ser)
                print("KT", utils.bbbstr(buff), utils.bytesval(buff, 0.1))
                time.sleep(0.1)

                buff = read_datapoint(0x0804, 2, ser)
                print("WW", utils.bbbstr(buff), utils.bytesval(buff, 0.1))
                time.sleep(1)


        # write test
        if(False):
            buff = read_datapoint(0x27d4, 1, ser)
            currval = buff
            print("Niveau Ist", utils.bbbstr(buff), bytesval(buff))
            
            time.sleep(1)

            data = bytes([50])
            ret = write_datapoint(0x27d4, data, ser)
            print("write succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x27d4, 1, ser)
            print("Niveau neu", utils.bbbstr(buff), bytesval(buff))

            time.sleep(1)

            ret = write_datapoint(0x27d4, currval, ser)
            print("write back succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x27d4, 1, ser)
            print("Niveau read back", utils.bbbstr(buff), bytesval(buff))

    
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except Exception as e:
        print(e)
    finally:
        # Serial Port schliessen
        if ser.is_open:
            print("exit close")
            # re-init KW protocol
            ser.write(bytes([0x04]))
            ser.close()


if __name__ == "__main__":
    main()
