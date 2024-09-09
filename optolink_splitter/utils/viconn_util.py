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

import serial
import time

from optolink_splitter.config_model import SplitterConfig
from optolink_splitter.optolinkvs2 import receive_vs2telegr
from optolink_splitter.utils.common_utils import bbbstr

# Funktion zum Hinzufügen von Bytes zum Puffer
def add_to_ringbuffer(buffer, new_bytes):
    for byte in new_bytes:
        buffer.pop(0)  # Entferne das erste Byte (das älteste Byte)
        buffer.append(byte)  # Füge das neue Byte am Ende hinzu


def log_vito(data, format_data_hex_format: str, pre, vitolog):
    if vitolog is not None:
        sd = bbbstr(data, format_data_hex_format)
        vitolog.write(f"{pre}\t{int(time.time()*1000)}\t{sd}\n")


# VS detection ---------------
def detect_vs2(
    config: SplitterConfig, serVicon: serial.Serial, serOpto: serial.Serial, timeout: float, vitolog_loc
) -> bool:
    bufferVicon = bytearray([0xFF, 0xFF, 0xFF])
    bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

    timestart = time.time()

    while True:
        # Lesen von Daten von beiden seriellen Schnittstellen
        dataVicon = serVicon.read()
        dataOpto = serOpto.read()

        fdata = False

        # Überprüfen, ob Daten von ser1 empfangen wurden und dann auf ser2 schreiben
        if dataVicon:
            serOpto.write(dataVicon)
            add_to_ringbuffer(bufferVicon, dataVicon)
            # optolinkvs2_switch.log_vito(dataVicon, "M")  # funktioniert hier nicht!?!?
            log_vito(dataVicon, config.format_data_hex_format, "M", vitolog_loc)
            fdata = True
            # reset optobuffer
            bufferOpto = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        # Überprüfen, ob Daten von ser2 empfangen wurden und dann auf ser1 schreiben
        if dataOpto:
            serVicon.write(dataOpto)
            add_to_ringbuffer(bufferOpto, dataOpto)
            # optolinkvs2_switch.log_vito(dataOpto, "S")  # funktioniert hier nicht!?!?
            log_vito(dataOpto, config.format_data_hex_format, "S", vitolog_loc)
            fdata = True
            # check VS2
            if bufferVicon == bytearray([0x16, 0x00, 0x00]):
                if dataOpto == b"\x06":
                    # Initialisierungssequenz erkannt und positive Antwort
                    return True
            if bufferOpto[0] == 0x06:
                if bufferOpto[1] == 0x41:
                    if bufferOpto[3] == 0x01:
                        # Antwort im VS2 Format erkannt
                        return True
        time.sleep(0.001)
        if time.time() > timestart + timeout:
            return False


# viconn request mechanism -------------
vicon_request = bytearray()


def listen_to_Vitoconnect(config: SplitterConfig, servicon: serial, vitolog_loc):
    global vicon_request
    while True:
        succ, _, data = receive_vs2telegr(config.format_data_hex_format, config.logging_show_opto_rx,
            False, True, servicon
        )  # contains sleep(0.005)
        if succ == 1:
            vicon_request = data
        elif data:
            log_vito(data, config.format_data_hex_format, "X", vitolog_loc)


def get_vicon_request() -> bytearray:
    global vicon_request
    ret = vicon_request
    vicon_request = bytearray()
    return ret
