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

from datetime import datetime
import settings_ini

# utils +++++++++++++++++++++++++++++
def get_int(v) -> int:
    if type(v) is int:
        return v
    return int(str(v), 0)

def to_number(v):
    s = str(v)
    try:
        return int(s, 0)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            #raise ValueError("Ungültige Zeichenkette für Umwandlung in eine Zahl")
            return None

def get_bool(v) -> bool:
    if(isinstance(v, bool)):
        return bool(v)
    if(str(v).lower() == 'true'):
        return True
    else:
        return False


def bytesval(data, scale=1, signd=False):
    val = int.from_bytes(data, byteorder='little', signed=signd)
    if(scale != 1):
        val = round(val * scale, settings_ini.max_decimals)
    return val


def bbbstr(data):
    try:
        return ' '.join([format(byte, settings_ini.data_hex_format) for byte in data])
    except:
        return data

def arr2hexstr(data):
    return ''.join([format(byte, settings_ini.data_hex_format) for byte in data])

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

def vdatetime2str(data:bytes) -> str:
    try:
        weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        wkd = weekdays[int(data[4]) - 1]
        dt = f"{data[3]:02x}.{data[2]:02x}.{data[0]:02x}{data[1]:02x}"
        tm = f"{data[5]:02x}:{data[6]:02x}:{data[7]:02x}"
        return f"{wkd} {dt} {tm}"
    except:
        return "(conversion failed)"

def utf82str(data:bytes) -> str:
    ret = data.decode("utf-8")
    return ret.replace('\x00', '')

def utf162str(data:bytes) -> str:
    ret = data.decode("utf-16")
    return ret.replace('\x00', '')

def unixtime2str(data) -> str:
    if(len(data) <= 4):
        return str(datetime.fromtimestamp(int.from_bytes(data, byteorder="little", signed=False)))
    else:
        dval = int.from_bytes(data, byteorder="little", signed=False)
        return f"{datetime.fromtimestamp(dval//1000)}.{dval%1000}"

