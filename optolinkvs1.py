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
# Optolink VS1 / KW Protocol, mainly virtual r/w datapoints
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# sync timer - if no comm for 500ms -> await new sync -----------
SYNC_TIMEOUT = 0.6
last_comm = 0.0

def reset_sync():
    global last_comm
    last_comm = time.monotonic()

def sync_elapsed(timeout = SYNC_TIMEOUT) -> bool:
    return (time.monotonic() > last_comm + timeout) 

# protocol -----------

def init_protocol(ser:serial.Serial) -> bool:
    # after the serial port read buffer is emptied
    ser.reset_input_buffer()
    # then an EOT (0x04) is send
    ser.write(bytes([0x04]))
    # and for 30x100ms waited for an ENQ (0x05)
    if(not wait_for_05(ser)):
        return False
    # now read F8 with STX
    outbuff = bytes([0x01, 0xF7, 0x00, 0xF8, 0x04])
    ser.reset_input_buffer()
    ser.write(outbuff)
    retcd,_,_ = receive_resp_telegr(4,0xF8,ser)
    ret = (retcd == 0x01) 
    #print("init_protocol vs1", ret)
    return ret


def re_init(ser:serial.Serial) -> bool:
    # after the serial port read buffer is emptied
    ser.reset_input_buffer()
    # then an EOT (0x04) is send
    ser.write(bytes([0x04]))
    # and for 30x100ms waited for an ENQ (0x05)
#    return wait_for_05(ser)  #TEMP
    ret = wait_for_05(ser)
    print("re_init", ret)
    return ret


def wait_for_05(ser:serial.Serial) -> bool:
    # and for 30x100ms waited for an ENQ (0x05) - we do 300x10ms (1 byte @4800 ca. 0.002s)
    for _ in range(30):
        time.sleep(0.1)
        try:
            buff = ser.read(1)
            if(settings.show_opto_rx):
                print(buff)
        except: 
            return False
        #print(buff)
        if(len(buff) > 0) and (int(buff[0]) == 0x05):
            return True
    logger.error("Timeout waiting for 0x05")
    return False
    

# virtiual read/write -----------

def read_datapoint(addr:int, rdlen:int, ser:serial.Serial) -> bytes:
    _,_,data = read_datapoint_ext(addr, rdlen, ser)
    return data

def read_datapoint_ext(addr:int, rdlen:int, ser:serial.Serial) -> tuple[int, int, bytearray]: 
    # returns: ReturnCode, Addr, Data
    rdlen = rdlen & 0xFF  # is byte
    outbuff = bytearray(4)
    outbuff[0] = 0xF7   # 0xF7 Virtual_READ
    outbuff[1] = (addr >> 8) & 0xFF  # hi byte
    outbuff[2] = addr & 0xFF         # lo byte
    outbuff[3] = rdlen  # Anzahl der zu lesenden Daten-Bytes

    if(sync_elapsed()):
        outbuff = bytearray([0x01]) + outbuff  # add STX
        re_init(ser)

    ser.reset_input_buffer()
    # After message is send, 
    ser.write(outbuff)
    #print("R tx", utils.bbbstr(outbuff))  #temp!
    # return retcode, addr, data
    return receive_resp_telegr(rdlen, addr, ser)


def write_datapoint(addr:int, data:bytes, ser:serial.Serial) -> bool:
    retcode,_,_ = write_datapoint_ext(addr, data, ser)
    return (retcode == 0x01)

def write_datapoint_ext(addr:int, data:bytes, ser:serial.Serial) -> tuple[int, int, bytearray]:
    wrlen = len(data)
    outbuff = bytearray(wrlen+4)
    outbuff[0] = 0xF4   # 0xF4 Virtual_WRITE 
    outbuff[1] = (addr >> 8) & 0xFF  # hi byte
    outbuff[2] = addr & 0xFF         # lo byte
    outbuff[3] = wrlen  # Anzahl der zu schreibenden Daten-Bytes
    for i in range(int(wrlen)):
        outbuff[4 + i] = data[i]

    if(sync_elapsed()):
        outbuff = bytearray([0x01]) + outbuff  # add STX
        re_init(ser)

    ser.reset_input_buffer()
    ser.write(outbuff)
    #print("W tx", utils.bbbstr(outbuff)) #temp!
    # return retcode, addr, data
    return receive_resp_telegr(wrlen, addr, ser)


# mainly internal, receive a response @ known length
def receive_resp_telegr(rlen:int, addr:int, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:  # type: ignore
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, AA=HandleLost, FF=TimeOut (all hex)
    # receives the V1 response to a Virtual_READ or Virtual_WRITE request @ known length
    i = 0
    inbuff = bytearray()

    # for up 20x50ms serial data is read. (we do 400x5ms)
    for _ in range(400):
        time.sleep(0.005)
        try:
            inbytes = ser.read_all()
            if(inbytes):
                inbuff += inbytes
                #print("rx", utils.bbbstr(inbuff))
        except: 
            return 0xAA, addr, inbuff

        # ggf. gleich durchleiten 
        if(ser2 is not None):
            if(inbytes):
                ser2.write(inbytes)
        
        # 'evaluate'
        if(len(inbuff) >= rlen):
            if(settings.show_opto_rx):
                print("rx", utils.bbbstr(inbuff))
            reset_sync()
            return 0x01, addr, inbuff[0:rlen]

    # timout
    if(settings.show_opto_rx):
        print("rx telegr timeout")
    return 0xFF, addr, inbuff


# receives anything...
def receive_telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:        # type: ignore
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, AA=HandleLost, FF=TimeOut (all hex)
    retcode, data = receive_fullraw(settings.fullraw_eot_time, settings.fullraw_timeout, ser, ser2)
    return retcode, 0, data  # 0x01?!?


def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, bytearray]:        # type: ignore
    # times in seconds
    inbuff = b''
    start_time = time.monotonic()
    last_receive_time = start_time

    while True:
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
            reset_sync()
            return 0x01, bytearray(inbuff)

        time.sleep(0.005)
        if(time.monotonic() > start_time + timeout):
            if(settings.show_opto_rx):
                print("rx fullraw timeout", utils.bbbstr(inbuff))
            return 0xFF, bytearray(inbuff)



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

        if not init_protocol(ser):
            raise Exception("init_vs1 failed.")
        
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
