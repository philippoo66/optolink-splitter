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
import threading

import utils
import settings_ini

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Optolink VS1 / KW Protocol, mainly virtual r/w datapoints
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# sync timer - if no comm for 500ms -> await new sync -----------
sync_elapsed = True    

def on_synctimer():
    global sync_elapsed   # sind die ganzen global nötig oder nimmt es sie auch so?
    sync_elapsed = True

timer_sync = threading.Timer(1.0, on_synctimer)

def reset_sync():
    global timer_sync
    global sync_elapsed
    secs = 0.5
    timer_sync.cancel()
    timer_sync = threading.Timer(secs, on_synctimer)
    timer_sync.start()
    sync_elapsed = False


# protocol -----------

def init_protocol(ser:serial.Serial) -> bool:
    # after the serial port read buffer is emptied
    ser.reset_input_buffer()
    # then an EOT (0x04) is send
    ser.write([0x04])
    # and for 30x100ms waited for an ENQ (0x05)
#    return wait_for_05(ser)
    ret = wait_for_05(ser)
    print("init_protocol vs1", ret)
    return ret

def wait_for_05(ser:serial.Serial) -> bool:
    # and for 30x100ms waited for an ENQ (0x05) - we do 300x10ms (1 byte @4800 ca. 0.002s)
    i = 0
    while(i < 300):
        time.sleep(0.01)
        try:
            buff = ser.read(1)
        except: return False
        #print(buff)
        if(len(buff) > 0):
            if(int(buff[0]) == 0x05):
                return True
        i+=1
    if(i == 300):
        print("Timeout waiting for 0x05")
        return False
    

# virtiual read/write -----------

def read_datapoint(addr:int, rdlen:int, ser:serial.Serial) -> bytes:
    _,_,data = read_datapoint_ext(addr, rdlen, ser)
    return data

def read_datapoint_ext(addr:int, rdlen:int, ser:serial.Serial) -> tuple[int, int, bytearray]: 
    global sync_elapsed
    rdlen = rdlen & 0xFF  # is byte
    outbuff = bytearray(4)
    outbuff[0] = 0xF7   # 0xF7 Virtual_READ
    outbuff[1] = (addr >> 8) & 0xFF  # hi byte
    outbuff[2] = addr & 0xFF         # lo byte
    outbuff[3] = rdlen  # Anzahl der zu lesenden Daten-Bytes

    if(sync_elapsed):
        outbuff = bytearray([0x01]) + outbuff  # add STX
        #wait_for_05(ser)
        init_protocol(ser)

    ser.reset_input_buffer()
    # After message is send, 
    ser.write(outbuff)
    print("R tx", utils.bbbstr(outbuff))  #temp!
    # return retcode, addr, data
    return receive_vs1telegr(rdlen, addr, ser)


def write_datapoint(addr:int, data:bytes, ser:serial.Serial) -> bool:
    retcode,_,_ = write_datapoint_ext(addr, data, ser)
    return (retcode == 0x01)

def write_datapoint_ext(addr:int, data:bytes, ser:serial.Serial) -> tuple[int, int, bytearray]:
    global sync_elapsed
    wrlen = len(data)
    outbuff = bytearray(wrlen+4)
    outbuff[0] = 0xF4   # 0xF4 Virtual_WRITE 
    outbuff[1] = (addr >> 8) & 0xFF  # hi byte
    outbuff[2] = addr & 0xFF         # lo byte
    outbuff[3] = wrlen  # Anzahl der zu schreibenden Daten-Bytes
    for i in range(int(wrlen)):
        outbuff[4 + i] = data[i]

    if(sync_elapsed):
        outbuff = bytearray([0x01]) + outbuff  # add STX
        #wait_for_05(ser)
        init_protocol(ser)

    ser.reset_input_buffer()
    ser.write(outbuff)
    print("W tx", utils.bbbstr(outbuff)) #temp!
    # return retcode, addr, data
    return receive_vs1telegr(wrlen, addr, ser)


# internal receive response @ known length
def receive_vs1telegr(rlen:int, addr:int, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, AA=HandleLost, FF=TimeOut (all hex)
    # receives the V1 response to a Virtual_READ or Virtual_WRITE request @ known length
    i = 0
    inbuff = bytearray()

    # for up 20x50ms serial data is read. (we do 400x5ms)
    while(True):
        time.sleep(0.005)
        try:
            inbytes = ser.read_all()
        except: return 0xAA, addr, inbytes
        inbuff += inbytes
        #print("rx", utils.bbbstr(inbuff))

        # ggf. gleich durchleiten 
        if(ser2 is not None):
            if(inbytes):
                ser2.write(inbytes)
        
        # 'evaluate'
        if(len(inbuff) >= rlen):
            if(settings_ini.show_opto_rx):
                print("rx", utils.bbbstr(inbuff))
            reset_sync()
            return 0x01, addr, inbuff[0:rlen]

        # timout
        i+=1
        if(i > 400):
            if(settings_ini.show_opto_rx):
                print("Timeout")
            return 0xFF, addr, inbuff


def receive_telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, AA=HandleLost, FF=TimeOut (all hex)
    # receives anything...
    data = receive_fullraw(settings_ini.fullraw_eot_time, settings_ini.fullraw_timeout, ser, ser2)
    return 0x01, 0, data  # 0x01?!?


def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> bytearray:
    # times in seconds
    data_buffer = b''
    start_time = time.time()
    last_receive_time = start_time

    while True:
        # Zeichen vom Serial Port lesen
        inbytes = ser.read_all()

        if inbytes:
            # Daten zum Datenpuffer hinzufügen
            data_buffer += inbytes
            last_receive_time = time.time()
            if(ser2 is not None):
                ser2.write(inbytes)
        elif data_buffer and ((time.time() - last_receive_time) > eot_time):
            # if data received and no further receive since more than eot_time
            if(settings_ini.show_opto_rx):
                print("rx", utils.bbbstr(data_buffer))
            return data_buffer

        time.sleep(0.005)
        if((time.time() - start_time) > timeout):
            if(settings_ini.show_opto_rx):
                print("rx timeout", utils.bbbstr(data_buffer))
            return data_buffer





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
        # Serial Port öffnen
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
            buff = read_datapoint(0x6300, 1, ser)
            currval = buff
            print("Soll Ist", utils.bbbstr(buff), bytesval(buff))
            
            time.sleep(1)

            data = bytes([50])
            ret = write_datapoint(0x6300, data, ser)
            print("write succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x6300, 1, ser)
            print("Soll neu", utils.bbbstr(buff), bytesval(buff))

            time.sleep(1)

            ret = write_datapoint(0x6300, currval, ser)
            print("write back succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x6300, 1, ser)
            print("Soll read back", utils.bbbstr(buff), bytesval(buff))

    
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except Exception as e:
        print(e)
    finally:
        # Serial Port schließen
        if ser.is_open:
            print("exit close")
            # re-init KW protocol
            ser.write([0x04])
            ser.close()


if __name__ == "__main__":
    main()
