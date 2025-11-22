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

# Serial Ports +++++++++++++++++++
port_optolink = '/dev/ttyUSB0'     # Serial port for Optolink device (mandatory, default: '/dev/ttyUSB0')
port_vitoconnect = '/dev/ttyAMA0'  # Serial port for Vitoconnect (optional, default: '/dev/ttyAMA0', set None if no Vitoconnect) Pls check https://github.com/philippoo66/optolink-splitter/wiki/520-termios.error:-(22,-'Invalid-argument')
vs2timeout = 120                   # Timeout (seconds) for VS2 protocol detection (default: 120)

# MQTT Connection ++++++++++++++++
mqtt = "192.168.0.123:1883"      # MQTT broker address (default: "192.168.0.123:1883", set None to disable MQTT)
mqtt_user = None                 # MQTT user credentials: "<user>:<pwd>" (default: None for anonymous access)
mqtt_logging = False             # dis/enables logging of paho.mqtt (default: False)

# MQTT Topics ++++++++++++++++++++
# Best practices recommendation: Always use lowercase for consistency and compatibility.
mqtt_topic = "Vito"              # MQTT topic for publishing data (default: "Vito")
mqtt_listen = "Vito/cmnd"        # MQTT topic for incoming commands (default: "Vito/cmnd", set None to disable)
mqtt_respond = "Vito/resp"       # MQTT topic for responses (default: "Vito/resp", set None to disable)
mqtt_fstr = "{dpname}"           # Format string for MQTT messages (default: "{dpname}", alternative e.g.: "{dpaddr:04X}_{dpname}")
mqtt_retain = False              # Publish retained messages. Last message per topic is stored on broker and sent to new/reconnecting subscribers. (default: False)
mqtt_no_redundant = False        # if True, no previously published unchanged messages 

# TCP/IP ++++++++++++++++++++++++++
tcpip_port = 65234               # TCP/IP port for communication (default: 65234, used by Viessdata; set None to disable TCP/IP)

# Optolink Communication Timing ++++
fullraw_eot_time = 0.05         # Timeout (seconds) to determine end of telegram (default: 0.05)
fullraw_timeout = 2             # Overall timeout (seconds) for receiving data (default: 2)
olbreath = 0.1                  # Pause (seconds) after a request-response cycle (default: 0.1)

# Optolink Logging ++++++++++++++
log_vitoconnect = False         # Enable logging of Vitoconnect Optolink rx+tx telegram communication (default: False)
show_opto_rx = True             # Display received Optolink data (default: True, no output when run as service)
viconn_to_mqtt = True           # Vitoconnect traffic published on MQTT
no_logger_file = False          # if true the optolinksvs2_switch.log will not get written

# Data Formatting +++++++++++++++
max_decimals = 4                # Max decimal places for float values (default: 4)
data_hex_format = '02x'         # Hexadecimal formatting (set '02X' for uppercase formatting, default: '02x')
resp_addr_format = 'x'          # Format of DP addresses in MQTT/TCPIP request responses ('d' for decimal, e.g. '04X' for 4-digit hex, default: 'x')

# Viessdata Utilities +++++++++++
write_viessdata_csv = False     # Enable writing Viessdata to CSV (default: False)
viessdata_csv_path = ""         # File path for Viessdata CSV output (default: "")
buffer_to_write = 60            # Buffer size before writing to CSV (default: 60)
dec_separator = ","             # Decimal separator for CSV output (default: ",")

# special for wo1c: read daily/weekly energy statistics +++++++++++
wo1c_energy = 0                 # 0:disabled, €N: every n-th cycle

# 1-Wire Sensors +++++++++++++++
# A typical sensor for temperature could be DS18B20; please mind that GPIO must be enabled for 1-Wire sensors (see Optolink-Splitter Wiki)
# Dictionary for 1-Wire sensor configuration (default: empty dictionary)
w1sensors = {                  
    # Addr: ('<w1_folder/sn>', '<slave_type>'),   # entry format
#     0xFFF4: ('28-3ce1d4438fd4', 'ds18b20'),     # Example sensor (highest known Optolink Address is 0xFF17)
#     0xFFFd: ('28-3ce1d443a4ed', 'ds18b20'),     # Another example sensor
}

# Datapoint Polling List+++++++++
poll_interval = 30              # Polling interval (seconds), 0 for continuous, -1 to disable (default: 30)
poll_items = [                  # Datapoints defined here will be polled; ignored if poll_list.py is found in the working directory
    # ([PollCycle,] Name, DpAddr, Length [, Scale/Type [, Signed]),
       # PollCycle:   Optional entry to allow the item to be polled only every x-th cycle
       # Name:        Datapoint name, published to MQTT as {dpname}; Best practices recommendation: Always use lowercase Names for consistency and compatibility.
       # DpAddr:      Address used to read the datapoint value (hex with '0x' or decimal)
       # Length:      Number of bytes to read
       # Scale/Type:  Optional; if omitted, value returns as a hex byte string without '0x'. See Wiki for details
       # Signed:      Numerical data will interpreted as signed (True) or unsigned (False, default is False if not explicitly set)
   
    # Example for Vitocalxxx-G with Vitotronic 200 (Typ WO1C) (from 04/2012)
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
    (60, "cop", 0x1680, 1, 0.1, False), # Poll every 60th poll cycle (if poll_interval = 30 => 60 x 30 = every 30 minutes)

    # Example for Vitodens 300 B3HB
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
    # ("Frostgefahr", 0x2500, 22, 'b:16:16', 'bool'),
    # ("RTS_akt", 0x2500, 22, 'b:12:13', 0.1, True),
    # ("VL_Soll_M2", 0x3500, 22, 'b:17:18', 0.1, True),
    
    # # 1-wire
    # ("SpeicherTemp_oben", 0xFFFd),
    # ("RuecklaufTemp_Sensor", 0xFFF4),
]


