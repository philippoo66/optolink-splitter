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

import importlib
#from logger_util import logger

SETTINGS_MODULE = "settings_ini"

class SettingsAdapter:
    def __init__(self):
        self._settings_obj = None

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  Here we define all the settings and their default values 
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # These settings might get overwritten later by
        # - settings.setting = value
        # - calling set_settings("another_module")

        # Serial Ports +++++++++++++++++++
        self.port_optolink = '/dev/ttyUSB0'     # Serial port for Optolink device (mandatory, default: '/dev/ttyUSB0')
        self.port_vitoconnect = None            # Serial port for Vitoconnect (optional, default: '/dev/ttyAMA0', set None if no Vitoconnect) Pls check https://github.com/philippoo66/optolink-splitter/wiki/520-termios.error:-(22,-'Invalid-argument')
        self.vs2timeout = 120                   # Timeout (seconds) for VS2 protocol detection with Vitoconnect (default: 120)
        self.vs1protocol = False                # if True, VS1/KW protocol used

        # MQTT Connection ++++++++++++++++
        self.mqtt_broker = None                 # MQTT broker address (default: "192.168.0.123:1883", set None to disable MQTT)
        self.mqtt_user = None                   # MQTT user credentials: "meuser:mypwd" (default: None for anonymous access)
        self.mqtt_tls_enable = False            # True = connect via TLS (MQTT over TLS) (default: False)
        self.mqtt_tls_skip_verify = False       # Disables TLS cert + hostname verification (INSECURE; self-signed / lab only; Default = False)
        self.mqtt_tls_ca_certs = None           # MQTT TLS CA bundle path (default: None to use OS CA store)
        self.mqtt_tls_certfile =  None          # MQTT TLS client cert (mTLS) path (default: None for no client cert)
        self.mqtt_tls_keyfile  = None           # MQTT TLS client key (mTLS) path (default: None for
        self.mqtt_logging = False               # Enable/Disables logging of paho.mqtt (default: False)

        # MQTT Topics ++++++++++++++++++++
        self.mqtt_topic = "Vito"                # MQTT topic for publishing data (default: "Vito")
        self.mqtt_listen = "Vito/cmnd"          # MQTT topic for incoming commands (default: "Vito/cmnd", set None to disable)
        self.mqtt_respond = "Vito/resp"         # MQTT topic for responses (default: "Vito/resp", set None to disable)
        self.mqtt_fstr = "{dpname}"             # Format string for MQTT messages (default: "{dpname}", alternative e.g.: "{dpaddr:04X}_{dpname}")
        self.mqtt_retain = False                # Publish retained messages. Last message per topic is stored on broker and sent to new/reconnecting subscribers. (default: False)
        self.mqtt_no_redundant = False          # if True, no previously published unchanged messages 

        # TCP/IP ++++++++++++++++++++++++++
        self.tcpip_port =  65234                # TCP/IP port for communication (default: 65234, used by Viessdata; set None to disable TCP/IP)

        # Optolink Communication Timing ++++
        self.fullraw_eot_time =  0.05           # Timeout (seconds) to determine end of telegram (default: 0.05)
        self.fullraw_timeout =  2               # Overall timeout (seconds) for receiving data (default: 2)
        self.olbreath =  0.05                   # Pause (seconds) after a request-response cycle (default: 0.05)

        # Optolink Logging ++++++++++++++
        self.show_opto_rx = True                # Console output of received Optolink data (default: True, no output when run as service)
        self.log_optolink = False               # Enable logging of Optolink rx+tx communication (default: False)
        self.log_vitoconnect = False            # Enable logging of Vitoconnect Optolink rx+tx telegram communication (default: False)
        self.viconn_to_mqtt = True              # Vitoconnect traffic published on MQTT

        # Data Formatting +++++++++++++++
        self.max_decimals = 4                   # Max decimal places for float values (default: 4)
        self.data_hex_format = '02x'            # Hexadecimal formatting (set '02X' for uppercase formatting, default: '02x')
        self.resp_addr_format = 'x'             # Format of DP addresses in MQTT/TCPIP request responses ('d' for decimal, e.g. '04X' for 4-digit hex, default: 'x')
        self.retcode_format =  'd'              # Format of return code in MQTT/TCPIP requests ('d' for decimal, e.g. '02X' for 2-digit hex, default: 'd')

        # Viessdata Utilities +++++++++++
        self.write_viessdata_csv =  False       # Enable writing Viessdata to CSV (default: False)
        self.viessdata_csv_path =  ""           # File path for Viessdata CSV output (default: "")
        self.buffer_to_write =  60              # Buffer size before writing CSV (default: 60)
        self.dec_separator =  ","               # Decimal separator for CSV output (default: ",")

        # General Settings +++++++++++
        self.no_logger_file =  False            # if True the optolinksvs2_switch.log will not get written
        self.log_level = 20                     # DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50,
        self.max_restarts = 5                   # re-start limit. counter gets reset after 100 succesful poll cycles 
        self.restart_delay = 10                 # seconds delay before re-starting 
        self.max_vicon_tries = 3                # limit for vicon tries. if exceeded, continuing without vitoconnect. should be less than max_restarts
        self.max_comm_errors = 10               # optolink comm error threshold to init restart
        self.retry_counters_reset = 30          # minutes of sucessful operation to reset the retry counters 

        # special for wo1c: read daily/weekly energy statistics +++++++++++
        self.wo1c_energy = 0                    # 0:disabled, €N: every n-th cycle

        # 1-Wire Sensors +++++++++++++++
        self.w1sensors = {}                  

        # Datapoint Polling List +++++++++
        self.poll_interval = 30                 # Polling interval (seconds), 0 for continuous, -1 to disable (default: 30)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  now we apply given settings from settings_ini.py or any other parser
        self.set_settings(SETTINGS_MODULE)


    def set_settings(self, settings_module:str = '', reload:bool = False):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  Here we take the settings from a module if exist there, 
        #  otherwise keep value unchanged 
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        if settings_module:
            # try:
                self._settings_obj = importlib.import_module(settings_module)
            # except Exception as e:
            #     logger.error(f"importing settings module: {e}")
            #     return
        
        # if not self._settings_obj:
        #     logger.error("set_settings: no settings object set")
        #     return
        
        if reload:
            # try:
                self._settings_obj = importlib.reload(self._settings_obj)
            # except Exception as e:
            #     logger.error(f"reload settings module: {e}")
            #     return


        # General Settings +++++++++++
        # a later change of no_logger_file will not be effective since logger is already up then 
        self.no_logger_file = getattr(self._settings_obj, 'no_logger_file', self.no_logger_file)
        self.log_level = getattr(self._settings_obj, 'log_level', self.log_level)
        self.max_restarts = getattr(self._settings_obj, 'max_restarts', self.max_restarts)
        self.restart_delay = getattr(self._settings_obj, 'restart_delay', self.restart_delay)
        self.max_vicon_tries = getattr(self._settings_obj, 'max_vicon_tries', self.max_vicon_tries)
        self.max_comm_errors = getattr(self._settings_obj, 'max_comm_errors', self.max_comm_errors)               
        self.retry_counters_reset = getattr(self._settings_obj, 'retry_counters_reset', self.retry_counters_reset)               

        # Serial Ports +++++++++++++++++++
        self.port_optolink = getattr(self._settings_obj, 'port_optolink', self.port_optolink)
        self.port_vitoconnect = getattr(self._settings_obj, 'port_vitoconnect', self.port_vitoconnect)
        self.vs2timeout = getattr(self._settings_obj, 'vs2timeout', self.vs2timeout)
        self.vs1protocol = getattr(self._settings_obj, 'vs1protocol', self.vs1protocol)

        # MQTT Connection ++++++++++++++++
        self.mqtt_broker = getattr(self._settings_obj, 'mqtt', self.mqtt_broker)  # old
        self.mqtt_broker = getattr(self._settings_obj, 'mqtt_broker', self.mqtt_broker)
        self.mqtt_user = getattr(self._settings_obj, 'mqtt_user', self.mqtt_user)
        self.mqtt_tls_enable = getattr(self._settings_obj, 'mqtt_tls_enable', self.mqtt_tls_enable)
        self.mqtt_tls_skip_verify = getattr(self._settings_obj, 'mqtt_tls_skip_verify', self.mqtt_tls_skip_verify)
        self.mqtt_tls_ca_certs = getattr(self._settings_obj, 'mqtt_tls_ca_certs', self.mqtt_tls_ca_certs)
        self.mqtt_tls_certfile = getattr(self._settings_obj, 'mqtt_tls_certfile', self.mqtt_tls_certfile)
        self.mqtt_tls_keyfile  = getattr(self._settings_obj, 'mqtt_tls_keyfile', self.mqtt_tls_keyfile)
        self.mqtt_logging = getattr(self._settings_obj, 'mqtt_logging',  self.mqtt_logging)

        # MQTT Topics ++++++++++++++++++++
        self.mqtt_topic = getattr(self._settings_obj, 'mqtt_topic', self.mqtt_topic)
        self.mqtt_listen = getattr(self._settings_obj, 'mqtt_listen', self.mqtt_listen)
        self.mqtt_respond = getattr(self._settings_obj, 'mqtt_respond', self.mqtt_respond)
        self.mqtt_fstr = getattr(self._settings_obj, 'mqtt_fstr',self.mqtt_fstr)
        self.mqtt_retain = getattr(self._settings_obj, 'mqtt_retain', self.mqtt_retain)
        self.mqtt_no_redundant = getattr(self._settings_obj, 'mqtt_no_redundant', self.mqtt_no_redundant)

        # TCP/IP ++++++++++++++++++++++++++
        self.tcpip_port = getattr(self._settings_obj, 'tcpip_port', self.tcpip_port)

        # Optolink Communication Timing ++++
        self.fullraw_eot_time = getattr(self._settings_obj, 'fullraw_eot_time', self.fullraw_eot_time)
        self.fullraw_timeout = getattr(self._settings_obj, 'fullraw_timeout', self.fullraw_timeout)
        self.olbreath = getattr(self._settings_obj, 'olbreath', self.olbreath)

        # Optolink Logging ++++++++++++++
        self.show_opto_rx = getattr(self._settings_obj, 'show_opto_rx', self.show_opto_rx)
        self.log_optolink = getattr(self._settings_obj, 'log_optolink', self.log_optolink)
        self.log_vitoconnect = getattr(self._settings_obj, 'log_vitoconnect', self.log_vitoconnect)
        self.viconn_to_mqtt = getattr(self._settings_obj, 'viconn_to_mqtt', self.viconn_to_mqtt)

        # Data Formatting +++++++++++++++
        self.max_decimals = getattr(self._settings_obj, 'max_decimals', self.max_decimals)
        self.data_hex_format = getattr(self._settings_obj, 'data_hex_format', self.data_hex_format)
        self.resp_addr_format = getattr(self._settings_obj, 'data_hex_format', self.resp_addr_format)
        self.retcode_format = getattr(self._settings_obj, 'retcode_format', self.retcode_format)

        # Viessdata Utilities +++++++++++
        self.write_viessdata_csv = getattr(self._settings_obj, 'write_viessdata_csv', self.write_viessdata_csv)
        self.viessdata_csv_path = getattr(self._settings_obj, 'viessdata_csv_path', self.viessdata_csv_path)
        self.buffer_to_write = getattr(self._settings_obj, 'buffer_to_write', self.buffer_to_write)
        self.dec_separator = getattr(self._settings_obj, 'dec_separator', self.dec_separator)

        # special for wo1c: read daily/weekly energy statistics +++++++++++
        self.wo1c_energy = getattr(self._settings_obj, 'wo1c_energy', self.wo1c_energy)

        # 1-Wire Sensors +++++++++++++++
        self.w1sensors = getattr(self._settings_obj, 'w1sensors', self.w1sensors)

        # Datapoint Polling Interval +++++++++
        self.poll_interval = getattr(self._settings_obj, 'poll_interval', self.poll_interval)


# === for global use ==================
settings = SettingsAdapter()