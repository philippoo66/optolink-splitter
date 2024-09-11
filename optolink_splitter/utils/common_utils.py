"""
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
"""

from csv import DictReader, reader
from typing import Union


# utils +++++++++++++++++++++++++++++
def get_int(v) -> int:
    if type(v) is int:
        return v
    else:
        return int(eval(str(v)))


def to_number(v):
    s = str(v)
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            # raise ValueError("Ungültige Zeichenkette für Umwandlung in eine Zahl")
            return None


def get_bool(v) -> bool:
    if isinstance(v, bool):
        return bool(v)
    if str(v).lower() == "true":
        return True
    else:
        return False


def bytesval(
    data,
    format_max_decimals: Union[int, float],
    scale: Union[int, float] = 1,
    signd: bool = False,
) -> Union[int, float]:
    val = int.from_bytes(data, byteorder="little", signed=signd)
    if scale != 1:
        val = round(val * scale, format_max_decimals)
    return val


def bbbstr(data, format_data_hex_format: str) -> str:
    return " ".join([format(byte, format_data_hex_format) for byte in data])


def arr2hexstr(data, format_data_hex_format: str) -> str:
    return "".join([format(byte, format_data_hex_format) for byte in data])


def hexstr2arr(thestring: str) -> bytearray:
    # '776F726C64' -> bytearray(b'world') <class 'bytearray'>
    return bytearray.fromhex(thestring)


def str2hexstr(normal_str: str) -> str:
    # 'world' -> '776f726c64'
    byte_str = bytes(
        normal_str, "utf-8"
    )  # Konvertiere den normalen String in einen Byte-String
    hex_str = (
        byte_str.hex()
    )  # Konvertiere den Byte-String in einen hexadezimalen String
    return hex_str


def bstr2str(bytestring) -> str:
    # b'hello world' -> hello world <class 'str'>
    # b'68656C6C6F' -> 68656C6C6F <class 'str'>
    return bytestring.decode("utf-8")


def str2bstr(normal_str: str) -> bytes:
    # '68656C6C6F' -> b'68656C6C6F' <class 'bytes'>
    return bytes(normal_str, "utf-8")


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


def vdatetime2str(data: bytes) -> str:
    try:
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        wkd = weekdays[int(data[4]) - 1]
        dt = f"{data[3]:02x}.{data[2]:02x}.{data[0]:02x}{data[1]:02x}"
        tm = f"{data[5]:02x}:{data[6]:02x}:{data[7]:02x}"
        return f"{wkd} {dt} {tm}"
    except:
        return "(conversion failed)"


def utf82str(data: bytes) -> str:
    ret = data.decode("utf-8")
    return ret.replace("\x00", "")


def csv_to_dict_list(path: str) -> list[dict]:
    dict_list: list = []
    with open(path, mode="r", newline="", encoding="utf-8") as csvfile:
        csv_reader = DictReader(csvfile, delimiter=",")
        dict_list.extend(dict(row) for row in csv_reader)
    return dict_list


def csv_to_tuple_list(path: str) -> list[tuple]:
    tuple_list: list = []
    with open(path, mode="r", newline="", encoding="utf-8") as csvfile:
        csv_reader = reader(csvfile, delimiter=",")
        next(csv_reader)  # ignore csv header
        tuple_list.extend(tuple(row) for row in csv_reader)
    return tuple_list
