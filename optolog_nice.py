#!/usr/bin/python

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

# ++++++++++++++++++++++++++++++++++++++++++
# This script converts the optolink.log
# into a better readable format.
# ++++++++++++++++++++++++++++++++++++++++++

import re

INPUT_FILE = "optolink.log"
OUTPUT_FILE = "optolink_nice.log"

# Alles vor dem ersten ':' wird ignoriert, RX/TX case-insensitive, danach die Hex-Daten
line_re = re.compile(r"^([^:]*):\s*(rx|tx)\s+([0-9a-fA-F]+)$", re.IGNORECASE)

rx_buffer = []
rx_timestamp = None

def format_bytes(hex_string: str) -> str:
    return " ".join(
        hex_string[i:i+2]
        for i in range(0, len(hex_string), 2)
    )

def flush_rx(out):
    global rx_buffer, rx_timestamp
    if rx_buffer:
        joined = "".join(rx_buffer)
        out.write(f"{rx_timestamp}: rx: {format_bytes(joined)}\n")
        rx_buffer = []
        rx_timestamp = None

with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as fout:

    for line in fin:
        stripped = line.strip()
        m = line_re.match(stripped)

        # Nicht rx/tx → rx flushen, Zeile unverändert übernehmen
        if not m:
            flush_rx(fout)
            fout.write(line)
            continue

        timestamp, direction, data = m.groups()

        if direction == "rx":
            rx_buffer.append(data)
            rx_timestamp = timestamp
        else:  # tx
            flush_rx(fout)
            fout.write(f"{timestamp}: tx: {format_bytes(data)}\n")

    flush_rx(fout)

print("done")
