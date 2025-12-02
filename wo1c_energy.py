import serial
import datetime

import optolinkvs2
import utils
import mqtt_util

interval = 0

def read_energy(ser:serial.Serial, day_of_week=None):
    # read energy by RPC
    addr = 0xb800
    wkday = day_of_week if day_of_week else datetime.datetime.now().weekday()
    outbuff = bytearray(10)
    outbuff[0] = 0x41   # 0x41 Telegrammstart
    outbuff[1] = 0x07   # Len Payload
    outbuff[2] = 0x00   # 0x00 Anfrage
    outbuff[3] = 0x07   # 0x07 Remote_Proc_Req
    outbuff[4] = (addr >> 8) & 0xFF  # hi byte
    outbuff[5] = addr & 0xFF         # lo byte
    outbuff[6] = 0x02   # Anzahl der Daten-Bytes
    outbuff[7] = 0x02   # procedure#
    outbuff[8] = wkday  # day of week
    outbuff[9] = optolinkvs2.calc_crc(outbuff)

    ser.reset_input_buffer()
    # After message is send, 
    ser.write(outbuff)
    #print("R tx", utils.bbbstr(outbuff))

    # return retcode, addr, data
    retcode, addr, data = optolinkvs2.receive_telegr(True, True, ser)

    if((retcode == 1) and (len(data) > 20)):
        print(f"day {wkday}:", utils.bbbstr(data[12:-1]))
        # print(utils.bytesval(data[12:14], 10))
        # print(utils.bytesval(data[14:16], 10))
        # print(utils.bytesval(data[16:18], 10))
        # print(utils.bytesval(data[18:20], 10))
        # energy_heating_thermal
        # energy_heating_electric
        # energy_water_thermal
        # energy_water_electric
        pre = f"{day_of_week}/" if day_of_week else ''
        mqtt_util.publish_read(f"{pre}energy_heating_thermal", addr, utils.bytesval(data[12:14], 0.1))
        mqtt_util.publish_read(f"{pre}energy_heating_electric", addr, utils.bytesval(data[14:16], 0.1))
        mqtt_util.publish_read(f"{pre}energy_water_thermal", addr, utils.bytesval(data[16:18], 0.1))
        mqtt_util.publish_read(f"{pre}energy_water_electric", addr, utils.bytesval(data[18:20], 0.1))
    
    return retcode
