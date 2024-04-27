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


def bytesval(data, scale=1, signd=False):
    val = int.from_bytes(data, byteorder='little', signed=signd)
    if(scale != 1):
        val = round(val * scale, settings_ini.max_decimals)
    return val


def bbbstr(data):
    return ' '.join([format(byte, settings_ini.hex_format) for byte in data])


def arr2hexstr(data):
    return ''.join([format(byte, settings_ini.hex_format) for byte in data])

def hexstr2arr(thestring:str) -> bytearray:
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

