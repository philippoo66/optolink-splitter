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

###########################################
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ##     
##  ATTENTION! DO NOT EDIT THIS MODULE!  ##
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ##     
###########################################

import settings_ini


SETTINGS_OBJ = settings_ini

# Serial Ports +++++++++++++++++++
port_optolink = getattr(SETTINGS_OBJ, 'port_optolink', '/dev/ttyUSB0')
port_vitoconnect = getattr(SETTINGS_OBJ, 'port_vitoconnect', None)
vs2timeout = getattr(SETTINGS_OBJ, 'vs2timeout', 120)
vs1protocol = getattr(SETTINGS_OBJ, 'vs1protocol', False)

# MQTT Connection ++++++++++++++++
mqtt = getattr(SETTINGS_OBJ, 'mqtt', None)                      # MQTT broker address (default: "192.168.0.123:1883", set None to disable MQTT)
mqtt_user = getattr(SETTINGS_OBJ, 'mqtt_user', None)            # MQTT user credentials: "meuser:mypwd" (default: None for anonymous access)
mqtt_tls_enable = getattr(SETTINGS_OBJ, 'mqtt_tls_enable', False)            # True = connect via TLS (MQTT over TLS) (default: False)
mqtt_tls_skip_verify = getattr(SETTINGS_OBJ, 'mqtt_tls_skip_verify', False)  # Disables TLS cert + hostname verification (INSECURE; self-signed / lab only; Default = False)
mqtt_tls_ca_certs = getattr(SETTINGS_OBJ, 'mqtt_tls_ca_certs', None)         # MQTT TLS CA bundle path (default: None to use OS CA store)
mqtt_tls_certfile = getattr(SETTINGS_OBJ, 'mqtt_tls_certfile', None)         # MQTT TLS client cert (mTLS) path (default: None for no client cert)
mqtt_tls_keyfile  = getattr(SETTINGS_OBJ, 'mqtt_tls_keyfile', None)          # MQTT TLS client key (mTLS) path (default: None for
mqtt_logging = getattr(SETTINGS_OBJ, 'mqtt_logging', False)     # Enable/Disables logging of paho.mqtt (default: False)

# MQTT Topics ++++++++++++++++++++
mqtt_topic = getattr(SETTINGS_OBJ, 'mqtt_topic', "Vito")              # MQTT topic for publishing data (default: "Vito")
mqtt_listen = getattr(SETTINGS_OBJ, 'mqtt_listen', "Vito/cmnd")        # MQTT topic for incoming commands (default: "Vito/cmnd", set None to disable)
mqtt_respond = getattr(SETTINGS_OBJ, 'mqtt_respond', "Vito/resp")       # MQTT topic for responses (default: "Vito/resp", set None to disable)
mqtt_fstr = getattr(SETTINGS_OBJ, 'mqtt_fstr', "{dpname}")           # Format string for MQTT messages (default: "{dpname}", alternative e.g.: "{dpaddr:04X}_{dpname}")
mqtt_retain = getattr(SETTINGS_OBJ, 'mqtt_retain', False)              # Publish retained messages. Last message per topic is stored on broker and sent to new/reconnecting subscribers. (default: False)
mqtt_no_redundant = getattr(SETTINGS_OBJ, 'mqtt_no_redundant', False)        # if True, no previously published unchanged messages 

# TCP/IP ++++++++++++++++++++++++++
tcpip_port = getattr(SETTINGS_OBJ, 'tcpip_port', 65234)               # TCP/IP port for communication (default: 65234, used by Viessdata; set None to disable TCP/IP)

# Optolink Communication Timing ++++
fullraw_eot_time = getattr(SETTINGS_OBJ, 'fullraw_eot_time', 0.05)         # Timeout (seconds) to determine end of telegram (default: 0.05)
fullraw_timeout = getattr(SETTINGS_OBJ, 'fullraw_timeout', 2)             # Overall timeout (seconds) for receiving data (default: 2)
olbreath = getattr(SETTINGS_OBJ, 'olbreath', 0.05)                 # Pause (seconds) after a request-response cycle (default: 0.05)

# Optolink Logging ++++++++++++++
show_opto_rx = getattr(SETTINGS_OBJ, 'show_opto_rx', True)             # Console output of received Optolink data (default: True, no output when run as service)
log_vitoconnect = getattr(SETTINGS_OBJ, 'log_vitoconnect', False)         # Enable logging of Vitoconnect Optolink rx+tx telegram communication (default: False)
viconn_to_mqtt = getattr(SETTINGS_OBJ, 'viconn_to_mqtt', True)           # Vitoconnect traffic published on MQTT

# Data Formatting +++++++++++++++
max_decimals = getattr(SETTINGS_OBJ, 'max_decimals', 4)                # Max decimal places for float values (default: 4)
data_hex_format = getattr(SETTINGS_OBJ, 'data_hex_format', '02x')         # Hexadecimal formatting (set '02X' for uppercase formatting, default: '02x')
resp_addr_format = getattr(SETTINGS_OBJ, 'data_hex_format', 'x')          # Format of DP addresses in MQTT/TCPIP request responses ('d' for decimal, e.g. '04X' for 4-digit hex, default: 'x')
retcode_format = getattr(SETTINGS_OBJ, 'retcode_format', 'd')            # Format of return code in MQTT/TCPIP requests ('d' for decimal, e.g. '02X' for 2-digit hex, default: 'd')

# Viessdata Utilities +++++++++++
write_viessdata_csv = getattr(SETTINGS_OBJ, 'write_viessdata_csv', False)     # Enable writing Viessdata to CSV (default: False)
viessdata_csv_path = getattr(SETTINGS_OBJ, 'viessdata_csv_path', "")         # File path for Viessdata CSV output (default: "")
buffer_to_write = getattr(SETTINGS_OBJ, 'buffer_to_write', 60)            # Buffer size before writing to CSV (default: 60)
dec_separator = getattr(SETTINGS_OBJ, 'dec_separator', ",")             # Decimal separator for CSV output (default: ",")


# General Settings +++++++++++
no_logger_file = getattr(SETTINGS_OBJ, 'no_logger_file', False)          # if True the optolinksvs2_switch.log will not get written

# special for wo1c: read daily/weekly energy statistics +++++++++++
wo1c_energy = getattr(SETTINGS_OBJ, 'wo1c_energy', 0)                 # 0:disabled, €N: every n-th cycle

# 1-Wire Sensors +++++++++++++++
w1sensors = getattr(SETTINGS_OBJ, 'w1sensors', {})                  

# Datapoint Polling List+++++++++
poll_interval = getattr(SETTINGS_OBJ, 'poll_interval', 30)              # Polling interval (seconds), 0 for continuous, -1 to disable (default: 30)
