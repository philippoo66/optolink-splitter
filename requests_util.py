import optolinkvs2
import settings_ini


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
            #raise ValueError("Ungültige Zeichenkette für Umwandlung in eine Zahl")
            return None

def to_bool(s:str) -> bool:
    if(s.lower() == 'true'):
        return True
    else:
        return False


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

def get_valstr(data, frmat, signd) -> str:
    scale = to_number(frmat)
    if(scale is not None):
        return optolinkvs2.bytesval(data, scale, to_bool(signd))
    else:
        #TODO hier evtl weitere Formate umsetzen
        #return raw
        return arr2hexstr(data)

    

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


# 'main' functions +++++++++++++++++++++++++++++

# TCP, MQTT requests
def respond_to_request(request:str, serViDev) -> tuple[int, str]:   # retcode, string_to_pass 
    parts = request.split(';')
    numelms = len(parts)
    retstr = ""
    ret = 0
    if(numelms == 1):
        # full raw  "4105000100F80806"
        bstr = bytes.fromhex(parts[0])
        serViDev.reset_input_buffer()
        serViDev.write(bstr)
        #print("sent to OL:", bbbstr(bstr))
        data = optolinkvs2.receive_fullraw(settings_ini.tcpip_fullraw_eot_time,settings_ini.tcpip_fullraw_timeout, serViDev)
        retstr = arr2hexstr(data)
        ret = 0x01
        #print("recd fr OL:", bbbstr(data))
    elif(numelms > 1):
        cmnd = parts[0].lower() 
        if(cmnd == "raw"):  # "raw;4105000100F80806"
            bstr = bytes.fromhex(parts[1])
            serViDev.reset_input_buffer()
            serViDev.write(bstr)
            #print("sent to OL:", bbbstr(retstr))
            ret, _, data = optolinkvs2.receive_vs2telegr(True, True, serViDev)
            #print("recd fr OL:", ret, ',', bbbstr(data))
            retstr = str(ret) + ';' + arr2hexstr(data)
        elif(cmnd == "read"):  # "read;0x0804;1;0.1;False"
            ret, addr, data = optolinkvs2.read_datapoint_ext(get_int(parts[1]), int(parts[2]), serViDev)
            if(ret==1):
                if(numelms > 3):
                    signd = "False"
                    if(numelms > 4):
                        signd = parts[4]
                    retstr = get_valstr(data, parts[3], signd)
                else:
                    #return raw
                    retstr = arr2hexstr(data)
            elif(data):
                retstr = int.from_bytes(data, 'big')
            else:
                retstr = "?"
            retstr = str(ret) + ';' + str(addr) + ';' + str(retstr)
        elif(cmnd == "write"):  # "write;0x6300;1;48"
            #raise Exception("write noch nicht fertig") #TODO
            bval = get_int(parts[3]).to_bytes(int(parts[2]), 'big')
            ret, addr, data = optolinkvs2.write_datapoint_ext(get_int(parts[1]), bval, serViDev)
            if(ret == 1): 
                val = int.from_bytes(bval, 'big')
            elif(data):
                val = int.from_bytes(data, 'big')
            else:
                val = "?"
            retstr = str(ret) + ';' + str(addr) + ';' + str(val)
    return ret, retstr


vicon_request = bytearray()

def listen_to_Vitoconnect(servicon):
    global vicon_request
    while(True):
        succ, _, data = optolinkvs2.receive_vs2telegr(False, True, servicon)
        if(succ == 1):
            vicon_request = data

def get_ViconData() -> bytearray:
    global vicon_request
    ret = vicon_request
    vicon_request = bytearray()
    return ret

