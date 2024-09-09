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

from serial.tools import list_ports


def list_serial_ports() -> None:
    ports = list_ports.comports()
    if not ports:
        print("Keine seriellen Ports gefunden.")
    else:
        print("Verfügbare serielle Ports:")
        for port, desc, hwid in sorted(ports):
            print(f"{port}: {desc} [{hwid}]")


if __name__ == "__main__":
    list_serial_ports()
