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
port_vitoconnect = '/dev/ttyS0'  # '/dev/ttyS0'  older Pi:'/dev/ttyAMA0'  {optional} set None if no Vitoconnect
port_optolink = '/dev/ttyUSB0'   # '/dev/ttyUSB0'  {mandatory}

vs2timeout = 120                 # seconds to detect VS2 protocol on vitoconnect connection


# MQTT +++++++++++++++++++
mqtt = "192.168.0.123:1883"      # e.g. "192.168.0.123:1883"; set None to disable MQTT
mqtt_user = None                 # "<user>:<pwd>"; set None for anonymous connect
mqtt_topic = "Vito"              # "optolink"
mqtt_fstr = "{dpname}"           # "{dpaddr:04X}_{dpname}"
mqtt_listen = "Vito/cmnd"        # "optolink/cmnd"; set None to disable listening
mqtt_respond = "Vito/resp"       # "optolink/resp"


# TCP/IP +++++++++++++++++++
tcpip_port = 65234         # e.g. 65234 is used by Viessdataby default; set None to disable TCP/IP


# timing +++++++++++++++++++
fullraw_eot_time = 0.05    # seconds. time no receive to decide end of telegram 
fullraw_timeout = 2        # seconds. timeout, return in any case 
olbreath = 0.1             # seconds of sleep after request-response cycle

# logging, info +++++++++++++++++++
log_vitoconnect = False    # logs communication with Vitoconnect (rx+tx telegrams)
show_opto_rx = True        # display on screen (no output when ran as service)

# format +++++++++++++++++++
max_decimals = 4
data_hex_format = '02x'    # set to '02X' for capitals
resp_addr_format = 'd'     # format of DP address in MQTT/TCPIP request response; e.g. 'd': decimal, '04X': hex 4 digits

# Viessdata utils +++++++++++++++++++
write_viessdata_csv = False
viessdata_csv_path = ""
buffer_to_write = 60
dec_separator = ","

# 1-wire sensors +++++++++++++++++++
w1sensors = {}
#     # addr : ('<w1_folder/sn>', '<slave_type>'),
#     0xFFF4 : ('28-3ce1d4438fd4', 'ds18b20'),   # highest known Optolink addr is 0xff17
#     0xFFFd : ('28-3ce1d443a4ed', 'ds18b20'),
# }


# polling datapoints +++++++++++++++++++
poll_interval = 30      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # ([PollCycle,] Name, DpAddr, Len, Scale/Type, Signed)

    # Tabelle fuer Vitocalxxx-G mit Vitotronic 200 (Typ WO1C) (ab 04/2012)
    ("error", 0x0491, 1, 1, False),
    ("outside_temperature", 0x0101, 2, 0.1, True),
    ("hk1_mode", 0xB000, 1, 1, False),			# betriebsart bit 4,5,6,7 comfort  bit 1 spar bit 0
    ("hk1_requested_temperature", 0xA406, 2, 0.01, False),
    ("hk1_normal_temperature", 0x2000, 2, 0.1, False),
    ("hk1_reduced_temperature", 0x2001, 2, 0.1, False),
    ("hk1_party_temperature", 0x2022, 2, 0.1, False),
    ("hk1_temperature", 0x0116, 2, 0.1, False),
    ("hk1_pump", 0x048D, 1, 1, False),
    ("hk1_supply_temperature", 0x010A, 2, 0.1, False),
    ("hk1_supply_target_temperature", 0x1800, 2, 0.1, False),
    ("hk2_mode", 0xB001, 1, 1, False),
    ("hk2_requested_temperature", 0xA446, 2, 0.01, False),
    ("hk2_normal_temperature", 0x3000, 2, 0.1, False),
    ("hk2_reduced_temperature", 0x3001, 2, 0.1, False),
    ("hk2_party_temperature", 0x3022, 2, 0.1, False),
    ("hk2_temperature", 0x0117, 2, 0.1, False),
    ("hk2_pump", 0x048E, 1, 1, False),
    ("hk2_supply_temperature", 0x0114, 2, 0.1, False),
    ("hk2_supply_target_temperature", 0x1801, 2, 0.1, False),
    ("buffer_temperature", 0x010B, 2, 0.1, False),
    ("nc_cooling", 0x0492, 1, 1, False),
    ("primary_supply_temperature", 0xB400, 3, 'b:0:1', 0.1, True), # Datalänge 3,Byte 0-1 Temperatur, Byte 3 Sensorstatus: 0-OK, 6-Nicht vorhanden
    ("primary_return_temperature", 0xB401, 3, 'b:0:1', 0.1, True),
    ("secondary_supply_temperature", 0xB402, 3, 'b:0:1', 0.1, True),
    ("secondary_return_temperature", 0xB403, 3, 'b:0:1', 0.1, True),
    ("liquid_gas_temperature", 0xB404, 3, 'b:0:1', 0.1, True),
    ("evaporation_temperature", 0xB407, 3, 'b:0:1', 0.1, True),
    ("condensation_temperature", 0xB408, 3, 'b:0:1', 0.1, True),
    ("suction_gas_temperature", 0xB409, 3, 'b:0:1', 0.1, True),
    ("hot_gas_temperature", 0xB40A, 3, 'b:0:1', 0.1, True),
    ("superheating_target", 0xB40B, 3, 'b:0:1', 0.1, True),
    ("superheating", 0xB40D, 3, 'b:0:1', 0.1, True),
    ("suction_gas_pressure", 0xB410, 3, 'b:0:1', 0.1, True),
    ("hot_gas_pressure", 0xB411, 3, 'b:0:1', 0.1, True),
    ("primary_pump", 0xB420, 2, 1, False),
    ("secondary_pump", 0xB421, 2, 1, False),
    ("compressor", 0xB423, 2, 1, False),
    ("expansion_valve", 0xB424, 2, 1, False),
    ("nc_supply_temperature", 0x0119, 2, 0.1, False),
    ("nc_supply_target_temperature", 0x1804, 2, 0.1, False),
    ("eheater_power", 0x1909, 1, 3000, False),
    ("eheater_3_energy", 0x0588, 4,  0.0008333, False),
    ("eheater_6_energy", 0x0589, 4,  0.0016667, False),
    ("thermal_energy", 0x1640, 4, 0.1, False),
    ("electrical_energy", 0x1660, 4, 0.1, False),
    ("thermal_power", 0x16A0, 4, 1, False),
    ("electrical_power", 0x16A4, 4, 1, False),
    (60, "cop", 0x1680, 1, 0.1, False), # Nur jedes 60. mal pollen (wenn poll_interval=30 => 60 x 30 = alle 30 Minuten)


    # # Tabelle fuer eine Vitodens 300 B3HB
    # ("Anlagenzeit", 0x088E, 8, 'vdatetime'),
    # ("AussenTemp", 0x0800, 2, 0.1, True),
    # ("KesselTemp", 0x0802, 2, 0.1, False),
    # ("SpeicherTemp", 0x0804, 2, 0.1, False),
    # ("AbgasTemp", 0x0808, 2, 0.1, False),
    # ("AussenTemp_fltrd", 0x5525, 2, 0.1, True),
    # ("AussenTemp_dmpd", 0x5523, 2, 0.1, True),
    # ("AussenTemp_mixed", 0x5527, 2, 0.1, True),
    # ("Eingang STB-Stoerung", 0x0A82, 1, 1, False),
    # ("Brennerstoerung", 0x0884, 1, 1, False),
    # ("Fehlerstatus Brennersteuergeraet", 0x5738, 1, 1, False),
    # ("Brennerstarts", 0x088A, 4, 1, False),
    # ("Betriebsstunden", 0x08A7, 4, 2.7777778e-4, False),  # 1/3600
    # ("Stellung Umschaltventil", 0x0A10, 1, 1, False),
    # ("Ruecklauftemp_calcd", 0x0C20, 2, 0.01, False),
    # ("Pumpenleistung", 0x0A3C, 1, 1, False),
    # ("Volumenstrom", 0x0C24, 2, 0.1, False),  # eigentlich scale 1 aber für Viessdata Grafik
    # ("KesselTemp_soll", 0x555A, 2, 0.1, False),
    # ("BrennerLeistung", 0xA38F, 1, 0.5, False),
    # ("BrennerModulation", 0x55D3, 1, 1, False),
    # ("Status", 0xA152, 2, 1, False),
    # ("SpeicherTemp_soll_akt", 0x6500, 2, 0.1, False),
    # ("Speicherladepumpe", 0x6513, 1, 1, False),
    # ("Zirkulationspumpe", 0x6515, 2, 1, False),

    # # ByteBit filter examples
    # ("Frostgefahr, aktuelle RTS etc", 0x2500, 22, 'b:0:21::raw'),
    # ("Frostgefahr", 0x2500, 22, 'b:16:16::raw'),
    # ("RTS_akt", 0x2500, 22, 'b:12:13', 0.1, False),
    
    # # 1-wire
    # ("SpeicherTemp_oben", 0xFFFd),
    # ("RuecklaufTemp_Sensor", 0xFFF4),
]

