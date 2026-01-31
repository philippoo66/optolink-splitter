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

from pathlib import Path
from datetime import datetime
from c_settings_adapter import settings
from logger_util import logger
import threading


# hier zur Vermeidung von circular imports und weil hier von fast überall erreichbar
# Threading-Events zur Steuerung von Neustarts und Beenden
restart_event = threading.Event()
shutdown_event = threading.Event()


comm_errors = 0
def comm_error(is_error:bool):
    """Count OL comm errors and initiate re-start on threshold"""
    global comm_errors
    if is_error:
        comm_errors += 2
        if comm_errors >= 2 * settings.max_comm_errors:
            logger.error("Optolink comm error threshold reached - initiate re-start")
            restart_event.set()
    elif comm_errors > 0:
        comm_errors -= 1



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
            #raise ValueError("Ungueltige Zeichenkette fuer Umwandlung in eine Zahl")
            return None

def get_bool(v) -> bool:
    if(isinstance(v, bool)):
        return bool(v)
    if(str(v).lower() == 'true'):
        return True
    else:
        return False


def bytesval(data, scale=1.0, signd=False):
    val = int.from_bytes(data, byteorder='little', signed=signd)
    if(scale != 1.0):
        val = round(val * scale, settings.max_decimals)
    return val


def bbbstr(data):
    try:
        return ' '.join([format(byte, settings.data_hex_format) for byte in data])
    except:
        return data

def arr2hexstr(data):
    return ''.join([format(byte, settings.data_hex_format) for byte in data])

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

# ueberfluessig...
# def arr2bstr(data):
#     # b'68656C6C6F' -> 68656C6C6F <class 'str'>
#     if isinstance(data, bytes):
#         return data.decode('utf-8')
#     elif isinstance(data, bytearray):
#         return bytes(data).decode('utf-8')
#     else:
#         raise TypeError("Unsupported data type")

def clean_string(s:str) -> str:
    return (
            s.strip()
            .replace("\0", "")
            .replace("\r", "")
            .replace("\n", "")
            .replace('"', "")
            .replace("'", "")
        )

def vdatetime2str(data:bytes, fdowidx:int=1) -> str:
    try:
        weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        wkd = weekdays[int(data[4]) - fdowidx]
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


def get_module_modified_datetime(module) -> datetime:
    """
    Gibt das letzte Aenderungsdatum der .py-Datei eines importierten Moduls zurueck.
    Erwartet ein normales benutzerdefiniertes Modul.
    """
    try:
        module_path = Path(module.__file__).with_suffix(".py")
        return datetime.fromtimestamp(module_path.stat().st_mtime)
    except:
        return datetime.min
    

