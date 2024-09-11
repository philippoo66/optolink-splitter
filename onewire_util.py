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

import time
from typing import Any, Optional

# Pfad zum One-Wire-Slave-Verzeichnis
base_dir = "/sys/bus/w1/devices/"


def read_w1file(device_file):
    with open(device_file, "r") as f:
        lines = f.readlines()
    return lines


# 69 01 55 05 7f a5 a5 66 fa : crc=fa YES
# 69 01 55 05 7f a5 a5 66 fa t=22562


def read_ds18b20(
    device_file, logging_show_opto_rx: bool
) -> tuple[int, float]:  # retcode, temp_°C
    for _ in range(15):  # 3 sec
        try:
            lines = read_w1file(device_file)
            if lines[0].strip()[-3:] == "YES":
                # Extrahieren der Temperatur aus den Daten
                pos = lines[1].find("t=")
                if pos != -1:
                    temp_string = lines[1][pos + 2 :]
                    temp_c = float(temp_string) / 1000.0
                    if logging_show_opto_rx:
                        print("w1", lines[1][:pos])
                    return 0x01, temp_c
        except:
            pass
        time.sleep(0.2)
    return 0xFF, -999.999  # FF = timeout


def read_ds2423(device_file) -> tuple[int, list[int]]:  # retcode, counts
    for _ in range(15):  # 3 sec
        try:
            lines = read_w1file(device_file)
            if lines[0].strip()[-3:] == "YES":
                counts = []
                for line in lines[1:]:
                    # Extrahieren der Zählerwerte aus den Daten
                    if line.startswith("count"):
                        count_value = int(line.split("=")[1])
                        counts.append(count_value)
                if (
                    len(counts) == 4
                ):  # Stellen sicher, dass wir alle 4 Zählerwerte haben
                    return 0x01, counts
        except:
            pass
        time.sleep(0.2)
    return 0xFF, []  # FF = timeout


# 'main' function -----------------
def read_w1sensor(
    sensor_id, w1sensors: list[tuple], logging_show_opto_rx: bool
) -> Optional[tuple[int, Any]]:  # retcode, val/s
    for item in w1sensors:
        if item[0] == sensor_id:
            sensinfo = (item[1], item[2])
    device_file = base_dir + sensinfo[0] + "/w1_slave"
    if sensinfo[1].lower() == "ds18b20":
        return read_ds18b20(device_file, logging_show_opto_rx)
    elif sensinfo[1].lower() == "ds2423":
        return read_ds2423(device_file)
    return None
    # elif() to be continued for other w1 sensors...
