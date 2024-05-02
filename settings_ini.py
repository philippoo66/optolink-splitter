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

# serial ports +++++++++++++++++++
port_vitoconnect = '/dev/ttyS0' # '/dev/ttyS0'  older Pi:'/dev/ttyAMA0'  {optional} set None if no Vitoconnect
port_optolink = '/dev/ttyUSB0'  # '/dev/ttyUSB0'  {mandatory}


# MQTT +++++++++++++++++++
mqtt = "192.168.0.123:1883"     # e.g. "192.168.0.123:1883"; set None to disable MQTT
mqtt_user = None                # "<user>:<pwd>"
mqtt_topic = "Vitodens"         # "optolink"
mqtt_fstr = "{dpname}"          # "{dpaddr:04X}_{dpname}"
mqtt_listen = "Vitodens/cmnd"   # "optolink/cmnd"; set None to disable listening
mqtt_respond = "Vitodens/resp"  # "optolink/resp"


# TCP/IP +++++++++++++++++++
tcpip_port = 65234              # e.g. 65234 is used by Viessdataby default; set None to disable TCP/IP


# full raw timing
fullraw_eot_time = 0.05    # seconds. time no receive to decide end of telegram 
fullraw_timeout = 2        # seconds. timeout, return in any case 

# logging, info +++++++++++++++++++
log_vitoconnect = False    # logs communication with Vitoconnect (rx+tx telegrams)
show_opto_rx = True        # display on screen (no output when ran as service)

# format +++++++++++++++++++
max_decimals = 4
data_hex_format = '02x'    # set to '02X' for capitals
resp_addr_format = 'd'     # format of DP address in MQTT/TCPIP request response; e.g. 'd': decimal, '04X': hex 4 digits

# Viessdata utils +++++++++++++++++++
write_viessdata_csv = True
viessdata_csv_path = ""
dec_separator = ","


# polling datapoints +++++++++++++++++++
poll_interval = 30      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # (Name, DpAddr, Len, Scale/Type, Signed)

    # meine Viessdata Tabelle
    #088E;0800;0802;0804;0808;5525;5523;5527;0A82;0884;5738;088A;08A7;0A10;0C20;0A3C;0C24;555A;A38F;55D3;A152;6500;6513;6515;
    ("Anlagenzeit", 0x088E, 8, 'vdatetime'),

    ("AussenTemp", 0x0800, 2, 0.1, True),
    ("KesselTemp", 0x0802, 2, 0.1, False),
    ("SpeicherTemp", 0x0804, 2, 0.1, False),
    ("AbgasTemp", 0x0808, 2, 0.1, False),

    ("AussenTemp_fltrd", 0x5525, 2, 0.1, True),
    ("AussenTemp_dmpd", 0x5523, 2, 0.1, True),
    ("AussenTemp_mixed", 0x5527, 2, 0.1, True),

    ("Eingang STB-Stoerung", 0x0A82, 1, 1, False),
    ("Brennerstoerung", 0x0884, 1, 1, False),
    ("Fehlerstatus Brennersteuergeraet", 0x5738, 1, 1, False),

    ("Brennerstarts", 0x088A, 4, 1, False),
    ("Betriebsstunden", 0x08A7, 4, 2.7777778e-4, False),  # 1/3600

    ("Stellung Umschaltventil", 0x0A10, 1, 1, False),

    ("Ruecklauftemp_calcd", 0x0C20, 2, 0.01, False),
    ("Pumpenleistung", 0x0A3C, 1, 1, False),
    ("Volumenstrom", 0x0C24, 2, 0.1, False),  # eigentlich scale 1 aber für Viessdata Grafik

    ("KesselTemp_soll", 0x555A, 2, 0.1, False),
    ("BrennerLeistung", 0xA38F, 1, 1, False),
    ("BrennerModulation", 0x55D3, 1, 1, False),

    ("Status", 0xA152, 2, 1, False),
    ("SpeicherTemp_soll_akt", 0x6500, 2, 0.1, False),
    ("Speicherladepumpe", 0x6513, 1, 1, False),
    ("Zirkulationspumpe", 0x6515, 2, 1, False),
    # bis hierher meine Viessdata Tabelle --------

#    ("Frostgefahr, aktuelle RTS etc", 0x2500, 22, 'raw'),
    ("Frostgefahr, aktuelle RTS etc", 0x2500, 22, 'b:0:21::raw'),
    ("Frostgefahr", 0x2500, 22, 'b:16:16::raw'),
    ("RTS_akt", 0x2500, 22, 'b:12:13', 0.1, False),
]
