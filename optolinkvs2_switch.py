import serial
import binascii
import time
import threading
import importlib

import settings_ini
import optolinkvs2
import viessdata_util
import tcpip_util
#import mqtt_util

# request buffers
vicon_request = bytearray()
mqtt_request = bytearray()
#tcpip_request = bytearray()
#tcpip_request_string = ""

# utils +++++++++++++++++++++++++++++
def get_int(v) -> int:
    if type(v) is int:
        return v
    else:
        return int(eval(str(v)))

def to_number(s: str):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            raise ValueError("Ungültige Zeichenkette für Umwandlung in eine Zahl")

def bbbstr(data):
    return ' '.join([format(byte, '02X') for byte in data])

def arr2hexstr(data):
    return ''.join([format(byte, '02X') for byte in data])

def hexstr2str(thestring:str) -> bytearray:
    # '776F726C64' -> bytearray(b'world') <class 'bytearray'>
    return bytearray.fromhex(thestring)

def str2hexstr(normal_str: str) -> str:
    # 'world' -> '776f726c64'
    byte_str = bytes(normal_str, 'utf-8')  # Konvertiere den normalen String in einen Byte-String
    hex_str = byte_str.hex()  # Konvertiere den Byte-String in einen hexadezimalen String
    return hex_str

def bstr2str(bytestring) -> str:
    # b'hello world' -> hello world <class 'str'>
    # b'68656C6C6F' -> 68656C6C6F <class 'str'>
    return bytestring.decode('utf-8')

def str2bstr(normal_str:str) -> bytes:
    # '68656C6C6F' -> b'68656C6C6F' <class 'bytes'>
    return bytes(normal_str, 'utf-8')

# funktioniert auch nicht wie gedacht...
# def str2bstr(normal_str:str) -> bytes:
#     # '776f726c64' -> b'776f726c64'
#     return normal_str.hex()

# funktioniert nicht wie gedacht...
# def hexstr2bytes(hex_str: str) -> bytes:
#     # '776f726c64' -> b'776f726c64'
#     return bytes.fromhex(hex_str)

# überflüssig...
# def arr2bstr(data):
#     # b'68656C6C6F' -> 68656C6C6F <class 'str'>
#     if isinstance(data, bytes):
#         return data.decode('utf-8')
#     elif isinstance(data, bytearray):
#         return bytes(data).decode('utf-8')
#     else:
#         raise TypeError("Unsupported data type")

def olbreath(retcode:int):
    if(retcode <= 0x03):
        # success, err msg
        time.sleep(0.1)
    elif(retcode == 0xFF):
        # timeout
        pass
    else:
        # allow calming down
        time.sleep(0.5)

# polling list +++++++++++++++++++++++++++++
poll_pointer = 0
poll_data = [None] * len(settings_ini.poll_items)

def do_poll_item(idx:int, poll_data, ser:serial.Serial):
    item = settings_ini.poll_items[idx]  # (Name, DpAddr, Len, Scale/Type, Signed)  
    retcode, addr, data = optolinkvs2.read_datapoint_ext(item[1], item[2], ser)
    if(retcode == 0x01):
        #if(item[3] == "raw"):
        if isinstance(item[3], str):
            # return bytestring
            val = ''.join(format(v, '02x') for v in data)           
        else: 
            # is a number
            val = optolinkvs2.bytesval(data, item[3], item[4])
        poll_data[idx] = val
    olbreath(retcode)

    
def on_polltimer():
    global poll_pointer
    print("on_polltimer", poll_pointer)
    if(poll_pointer > len(settings_ini.poll_items)):
        poll_pointer = 0
    startPollTimer(settings_ini.poll_interval)

timer_pollinterval = threading.Timer(1.0, on_polltimer)

def startPollTimer(secs:float):
    global timer_pollinterval
    timer_pollinterval.cancel()
    timer_pollinterval = threading.Timer(secs, on_polltimer)
    timer_pollinterval.start()




# ------------------------
# Main
# ------------------------
def main():
    global poll_pointer
    global poll_data

    mod_mqtt_util = None

    # serielle Verbidungen mit Vitoconnect und dem Optolink Kopf aufbauen ++++++++++++++
    serViCon = None  # Vitoconnect (Master)
    serViDev = None  # Viessmann Device (Slave)

    if(settings_ini.port_vitoconnect is not None):
        serViCon = serial.Serial(settings_ini.port_vitoconnect,
                     baudrate=4800,
                     parity=serial.PARITY_EVEN,
                     stopbits=serial.STOPBITS_TWO,
                     bytesize=serial.EIGHTBITS,
                     timeout=0)
    
    if(settings_ini.port_optolink is not None):
        serViDev = serial.Serial(settings_ini.port_optolink,
                     baudrate=4800,
                     parity=serial.PARITY_EVEN,
                     stopbits=serial.STOPBITS_TWO,
                     bytesize=serial.EIGHTBITS,
                     timeout=0)

    if(serViCon is not None):
        # VS2 Protokoll erkennen
        pass #TODO
    else:
        # VS2 Protokoll am Slave initialisieren
        if(not optolinkvs2.init_vs2(serViDev)):
            print("init_vs2 failed")
            #TODO back to VS1, port schliessen etc <- done unten
            # if serViDev.is_open:
            #     print("exit close")
            #     # re-init KW protocol
            #     serViDev.write([0x04])
            #     serViDev.close()
            raise Exception("init_vs2 failed")


    # Empfangstask Vitoconnect starten
    
    # Empfangstask des (der) sekundären Master/s starten (TcpIp, MQTT)

    # MQTT --------
    if(settings_ini.mqtt is not None):
        # avoid paho.mqtt required if not used
        mod_mqtt_util = importlib.import_module("mqtt_util")
        mod_mqtt_util.connect_mqtt()
        #TODO listening thread

    # TCP/IP connection --------
    if(settings_ini.tcpip_port is not None):
        tcp_thread = threading.Thread(target=tcpip_util.tcpip4ever, args=(settings_ini.tcpip_port,True))
        tcp_thread.daemon = True  # Setze den Thread als Hintergrundthread - wichtig für Ctrl-C
        tcp_thread.start()

    # Polling Mechanismus --------
    len_polllist = len(settings_ini.poll_items)
    if(settings_ini.poll_interval > 0) and (len_polllist > 0):
        startPollTimer(settings_ini.poll_interval)


    # Main Loop starten und Sachen abarbeiten
    request_pointer = 0
    try:
        while(True):
            # first Vitoconnect request
            if(vicon_request):
                serViDev.write(vicon_request)
                # recive response an pass bytes directly back to VitoConnect, 
                # returns when response is complete (or error or timeout) 
                ret,_,_ = optolinkvs2.receive_vs2telegr(True, serViDev, serViCon)
                olbreath(ret)     

            # secondary requests ------------------
            #TODO überlegen, ob Vitoconnect request nicht auch in der Reihe reicht

            # polling list --------
            if(request_pointer == 0):              
                if(settings_ini.poll_interval < 0):
                    request_pointer += 1
                elif(poll_pointer < len_polllist):
                    do_poll_item(poll_pointer, poll_data, serViDev)
                    if(settings_ini.mqtt is not None):
                        # post to MQTT broker
                        item = settings_ini.poll_items[poll_pointer]  # (Name, DpAddr, Len, Scale/Type, Signed)  
                        mod_mqtt_util.showread(item[0], item[1], poll_data[poll_pointer])

                    poll_pointer += 1

                    if(poll_pointer == len_polllist):
                        if(settings_ini.write_viessdata_csv):
                            viessdata_util.write_csv_line(poll_data)
                        poll_pointer += 1
                        if(settings_ini.poll_interval == 0):
                            poll_pointer = 0
                else:
                    request_pointer += 1

            # MQTT request --------
            if(request_pointer == 1):
                if(settings_ini.mqtt is None): 
                    request_pointer += 1
                elif(mqtt_request):
                    #TODO
                    # eigentlich gleich wie TCP
                    pass
                else:
                    request_pointer += 1

            # TCP/IP request --------
            if(request_pointer == 2):
                if(settings_ini.tcpip_port is None):
                    request_pointer += 1
                else:
                    msg = tcpip_util.get_tcpdata()
                    if(msg):
                        try:
                            parts = msg.split(';')
                            numelms = len(parts)  
                            if(numelms == 1):
                                # full raw  "4105000100F80806"
                                bstr = bytes.fromhex(parts[0])
                                serViDev.reset_input_buffer()
                                serViDev.write(bstr)
                                print("sent to OL:", bbbstr(bstr))
                                data = optolinkvs2.receive_fullraw(settings_ini.tcpip_fullraw_eot_time,settings_ini.tcpip_fullraw_timeout, serViDev)
                                bstr = arr2hexstr(data)
                                print("recd fr OL:", bbbstr(data))
                                tcpip_util.send_tcpip(bstr)
                            elif(numelms > 1):
                                if(parts[0] == "raw"):  # "raw;4105000100F80806"
                                    bstr = bytes.fromhex(parts[1])
                                    serViDev.reset_input_buffer()
                                    serViDev.write(bstr)
                                    print("sent to OL:", bbbstr(bstr))
                                    ret, data = optolinkvs2.receive_vs2telegr_raw(True, serViDev)
                                    print("recd fr OL:", ret, ',', bbbstr(data))
                                    bstr = str(ret) + ';' + arr2hexstr(data)
                                    tcpip_util.send_tcpip(bstr)
                                elif(parts[0] == "read"):  # "read;0x0804;1;10;False"
                                    #raise Exception("nicht fertig") #TODO
                                    ret, addr, data = optolinkvs2.read_datapoint_ext(get_int(parts[1]), int(parts[2]), serViDev)
                                    if(numelms > 3):
                                        val = optolinkvs2.bytesval(data, to_number(parts[3]), bool(parts[4]))
                                    else:
                                        #return raw
                                        val = arr2hexstr(data)
                                    bstr = str(ret) + ';' + str(addr) + ';' + str(val)
                                    tcpip_util.send_tcpip(bstr)
                                elif(parts[0] == "write"):  # "write;0x6300;1;48"
                                    raise Exception("nicht fertig") #TODO
                                    bstr = get_int(parts[3]).to_bytes(int(parts[2]), 'big')
                                    ret, addr, _ = optolinkvs2.write_datapoint_ext(get_int(parts[1]), bstr, serViDev)
                                    bstr = str(ret) + ';' + str(addr)
                                    tcpip_util.send_tcpip(bstr)
                        except Exception as e:
                            print("Error handling TCP request:", e)
                    else:
                        request_pointer += 1

            # request_pointer control --------
            request_pointer += 1
            if(request_pointer > 2):
                request_pointer = 0
            
            # let cpu take a breath
            time.sleep(0.01)  #TODO runter setzen

    except KeyboardInterrupt:
        print("Abbruch durch Benutzer.")
    finally:
        # Schließen der seriellen Schnittstellen, Ausgabedatei, PollTimer, 
        print("exit close")
        if(serViCon is not None):
            print("closing serViCon")
            serViCon.close()
        if(serViDev is not None):
            if serViDev.is_open:
                print("closing serViDev")
                # re-init KW protocol
                #serViDev.write([0x04])  #TODO yes or no?
                serViDev.close()
        print("cancel poll timer ") 
        timer_pollinterval.cancel()
        tcpip_util.exit_tcpip()
        #tcp_thread.join()  #TODO ??
        if(settings_ini.mqtt is not None):
            mod_mqtt_util.exit_mqtt()

    # sauber beenden: Tasks stoppen, VS1 Protokoll aktivieren(?), alle Verbindungen trennen

if __name__ == "__main__":
    main()
