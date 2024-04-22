import serial
import sys
import time

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Optolink VS2 / 300 Protocol, mainly virtual r/w datapoints
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def init_vs2(ser:serial.Serial) -> bool:

    # after the serial port read buffer is emptied
    ser.reset_input_buffer()

    # then an EOT (0x04) is send
    ser.write([0x04])

    # and for 30x100ms waited for an ENQ (0x05)
    i = 0
    while(i < 30):
        time.sleep(0.1)
        buff = ser.read(1)
        print(buff)
        if(len(buff) > 0):
            if(int(buff[0]) == 0x05):
                break
        i+=1

    if(i == 30):
        print("init_vs2: Timeout waiting for 0x05")
        return False
    
    ser.reset_input_buffer()

    # after which a VS2_START_VS2, 0, 0 (0x16,0x00,0x00) is send
    ser.write([0x16,0x00,0x00])

    # and within 30x100ms an VS2_ACK (0x06) is expected.
    i = 0
    while(i < 30):
        time.sleep(0.1)
        buff = ser.read(1)
        if(len(buff) > 0):
            if(int(buff[0]) == 0x06):
                break
        i+=1

    if(i == 30):
        print("init_vs2: Timeout waiting for 0x06")
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
    print("R tx", bbbstr(outbuff))

    #retcode, addr, data = receive_vs2telegr(True, ser)
    #return retcode, addr, data
    return receive_vs2telegr(True, False, ser)


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
    print("W tx", bbbstr(outbuff))

    #retcode, addr, data = receive_vs2telegr(True, ser)
    #return retcode, addr, data
    return receive_vs2telegr(True, False, ser)


'''
def receive_vs2telegr(resptelegr:bool, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:
    # returns: ReturnCode, DpAddress, Data
    # ReturnCode: 01=success, 03=ErrMsg, 15=NACK, 20=UnknB0_Err, 41=STX_Err, FD=PlLen_Err, FE=CRC_Err, FF=TimeOut (all hex)
    # receives the V2 response to a Virtual_READ or Virtual_WRITE request
    i = 0
    state = 0
    inbuff = bytearray()
    valdata = bytearray()
    # for up 30x100ms serial data is read. (we do 300x10ms)
    while(True):
        time.sleep(0.01)
        #try:
        inbytes = ser.read(ser.in_waiting)
        #except: return 0, bytearray()
        inbuff += inbytes
        
        # ggf. gleich durchleiten 
        if(ser2 is not None):
            if(inbytes):
                ser2.write(inbytes)
        
        # evaluate
        if(state == 0):
            if(resptelegr):
                if(len(inbuff) > 0):
                    print("rx", format(inbuff[0], '02X'))
                    if(inbuff[0] == 0x06): # VS2_ACK
                        state = 1
                    elif (inbuff[0] == 0x15): # VS2_NACK
                        print("NACK Error")
                        return 0x15, 0, []       # hier müsste ggf noch ein eventueller Rest des Telegrams abgewartet werden 
                    else:
                        print("unknown first byte Error")
                        return 0x20, 0, []
                    # erstes Byte abtrennen
                    inbuff = inbuff[1:]
            else:
                state = 1
        
        # ab hier Master Request und Slave Response identischer Aufbau (abgesehen von Error Message und sowas)
        if(state == 1):
            if(len(inbuff) > 1):
                if(inbuff[0] != 0x41): # STX
                    print("STX Error")
                    return 0x41, 0, []  # hier müsste ggf noch ein eventueller Rest des Telegrams abgewartet werden
                state = 2

        if(state == 2):
            if(len(inbuff) > 2):  # STX, Len
                pllen = inbuff[1]
                if(pllen < 5):  # FnctCode + MsgId + AddrHi + AddrLo + BlkLen
                    print("rx", bbbstr(inbuff))
                    print("PL Len Error", pllen)
                    return 0xFD, 0, []
                if(len(inbuff) >= pllen+3):  # STX + Len + Payload + CRC
                    print("rx", bbbstr(inbuff))
                    inbuff = inbuff[:pllen+4]  # make sure no tailing trash 
                    addr = (inbuff[4] << 8) + inbuff[5]
                    valdata = inbuff[7:pllen+2]   # STX + Len + FnctCode + MsgId + AddrHi + AddrLo + BlkLen (+ Data) + CRC
                    if(inbuff[-1] != calc_crc(inbuff)):
                        print("CRC Error")
                        return 0xFE, addr, valdata
                    if(inbuff[2] & 0x0F == 0x03):
                        print("Error Message", bbbstr(valdata))
                        return 0x03, addr, valdata
                    # success
                    return 0x01, addr, valdata 
        # timout
        i+=1
        if(i > 300):
            print("Timeout")
            return 0xFF, 0, inbuff
'''

def receive_vs2telegr(resptelegr:bool, raw:bool, ser:serial.Serial, ser2:serial.Serial=None) -> tuple[int, int, bytearray]:
    # returns: ReturnCode, Addr, Data
    # ReturnCode: 01=success, 03=ErrMsg, 15=NACK, 20=UnknB0_Err, 41=STX_Err, AA=HandleLost, FD=PlLen_Err, FE=CRC_Err, FF=TimeOut (all hex)
    # receives the V2 response to a Virtual_READ or Virtual_WRITE request
    i = 0
    state = 0
    inbuff = bytearray()
    alldata = bytearray()
    retdata = bytearray()
    addr = 0

    # for up 30x100ms serial data is read. (we do 300x10ms)
    while(True):
        time.sleep(0.005)
        try:
            inbytes = ser.read(ser.in_waiting)
        except: return 0xAA, 0, retdata
        inbuff += inbytes
        alldata += inbytes

        # ggf. gleich durchleiten 
        if(ser2 is not None):
            if(inbytes):
                ser2.write(inbytes)
        
        # evaluate
        if(state == 0):
            if(resptelegr):
                if(len(inbuff) > 0):
                    print("rx", format(inbuff[0], '02X'))
                    if(inbuff[0] == 0x06): # VS2_ACK
                        state = 1
                    elif(inbuff[0] == 0x15): # VS2_NACK
                        print("NACK Error")
                        if(raw): retdata = alldata
                        return 0x15, 0, retdata       # hier müsste ggf noch ein eventueller Rest des Telegrams abgewartet werden 
                    else:
                        print("unknown first byte Error")
                        if(raw): retdata = alldata
                        return 0x20, 0, retdata
                    # erstes Byte abtrennen
                    inbuff = inbuff[1:]
            else:
                state = 1
        
        # ab hier Master Request und Slave Response identischer Aufbau (abgesehen von Error Message und sowas)
        if(state == 1):
            if(len(inbuff) > 0):
                if(inbuff[0] != 0x41): # STX
                    print("STX Error")
                    if(raw): retdata = alldata
                    return 0x41, 0, retdata  # hier müsste ggf noch ein eventueller Rest des Telegrams abgewartet werden
                state = 2

        if(state == 2):
            if(len(inbuff) > 1):  # STX, Len
                pllen = inbuff[1]
                if(pllen < 5):  # FnctCode + MsgId + AddrHi + AddrLo + BlkLen
                    print("rx", bbbstr(alldata))
                    print("PL Len Error", pllen)
                    if(raw): retdata = alldata
                    return 0xFD, 0, retdata
                if(len(inbuff) >= pllen+3):  # STX + Len + Payload + CRC
                    print("rx", bbbstr(alldata))
                    inbuff = inbuff[:pllen+4]  # make sure no tailing trash 
                    addr = (inbuff[4] << 8) + inbuff[5]  # my be bullshit in case of raw
                    retdata = inbuff[7:pllen+2]   # STX + Len + FnctCode + MsgId + AddrHi + AddrLo + BlkLen (+ Data) + CRC
                    if(inbuff[-1] != calc_crc(inbuff)):
                        print("CRC Error")
                        if(raw): retdata = alldata
                        return 0xFE, addr, retdata
                    if(inbuff[2] & 0x0F == 0x03):
                        print("Error Message", bbbstr(retdata))
                        if(raw): retdata = alldata
                        return 0x03, addr, retdata
                    #success
                    if(raw): retdata = alldata
                    return 0x01, addr, retdata 
        # timout
        i+=1
        if(i > 600):
            print("Timeout")
            if(raw): retdata = alldata
            return 0xFF, addr, retdata

def receive_fullraw(eot_time, timeout, ser:serial.Serial, ser2:serial.Serial=None) -> bytearray:
    # times in seconds
    data_buffer = b''
    start_time = time.time()
    last_receive_time = time.time()

    while True:
        # Zeichen vom Serial Port lesen
        inbytes = ser.read()

        if inbytes:
            # Daten zum Datenpuffer hinzufügen
            data_buffer += inbytes
            last_receive_time = time.time()
            if(ser2 is not None):
                ser2.write(inbytes)
            #print(data_buffer.hex())
        elif data_buffer and ((time.time() - last_receive_time) > eot_time):
            # if data received and no further receive since more than eot_time
            #hex_data = ' '.join([format(byte, '02X') for byte in data_buffer])
            #print(hex_data)
            return data_buffer

        time.sleep(0.001)
        if((time.time() - start_time) > timeout):
            return data_buffer


def calc_crc(telegram) -> int:
    # CRC, a modulo-256 addition of bytes from Block Length and the additional bytes.
    CRCsum = 0
    telestart = 1
    teleend = telegram[1] + 1  # len payload + len byte itself

    # if telegram[0] != 0x41: # STX
    #     print("ugly STX", bbbstr(telegram))
    #     telestart += 1
    #     teleend = telegram[2] + 2
    #     if (telegram[0] != 0x06) and (telegram[1] != 0x41):
    #         print("ugly telegram", bbbstr(telegram))
    #         return 0  # 1:256 that it fits nevertheless

    for i in range(telestart, teleend + 1):
        CRCsum += telegram[i]

    return CRCsum % 0x100


def bbbstr(data):
    return ' '.join([format(byte, '02X') for byte in data])

def bytesval(data, scale, signd=False):
    return round(int.from_bytes(data, byteorder='little', signed=signd) * scale, 4)  # max 4 decimals 



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

        if not init_vs2(ser):
            raise Exception("init_vs2 failed.")
        
        # read test
        if(True):
            while(True):
                buff = read_datapoint(0x00f8, 8, ser)
                print("0x00f8", bbbstr(buff))
                time.sleep(0.1)

                buff = read_datapoint(0x0802, 2, ser)
                print("KT", bbbstr(buff), bytesval(buff, 0.1))
                time.sleep(0.1)

                buff = read_datapoint(0x0804, 2, ser)
                print("WW", bbbstr(buff), bytesval(buff, 0.1))
                time.sleep(1)


        # write test
        if(False):
            buff = read_datapoint(0x6300, 1, ser)
            currval = buff
            print("Soll Ist", bbbstr(buff), bytesval(buff))
            
            time.sleep(1)

            data = bytes([50])
            ret = write_datapoint(0x6300, data, ser)
            print("write succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x6300, 1, ser)
            print("Soll neu", bbbstr(buff), bytesval(buff))

            time.sleep(1)

            ret = write_datapoint(0x6300, currval, ser)
            print("write back succ", ret)

            time.sleep(2)

            buff = read_datapoint(0x6300, 1, ser)
            print("Soll read back", bbbstr(buff), bytesval(buff))

    
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