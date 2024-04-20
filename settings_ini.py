
# serial ports +++++++++++++++++++
port_vitoconnect = None  # "/dev/ttyS0"  older Pi:"/dev/ttyAMA0"
port_optolink = "COM4"   # "/dev/ttyUSB0"


# MQTT +++++++++++++++++++
mqtt = "192.168.1.115:1883"         # e.g. "192.168.0.1:1883"; set None to disable MQTT
mqtt_user = None  # "<user>:<pwd>"
mqtt_topic = "Vitodens"
mqtt_fstr = "{dpname}"  # "{dpaddr:04X}_{dpname}"
mqtt_listen = "optolink/cmnd"  # "optolink/cmnd"


# TCP/IP +++++++++++++++++++
tcpip_port = 65234   # e.g. 65234 is used by Viessdata; set None to disable TCP/IP
tcpip_fullraw_eot_time = 0.05  # seconds. time no receive decide end of telegram 
tcpip_fullraw_timeout = 2     # seconds. timeout, return in any case 


# polling datapoints +++++++++++++++++++
poll_interval = 30      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # (Name, DpAddr, Len, Scale/Type, Signed)
    ("AussenTemp", 0x0800, 2, 0.1, True),

    ("KesselTemp_soll", 0x555A, 2, 0.1, False),
    ("KesselTemp", 0x0802, 2, 0.1, False),
    ("BrennerModulation", 0x55D3, 1, 1, False),
    ("BrennerLeistung", 0xA38F, 1, 1, False),
    ("AbgasTemp", 0x0808, 2, 0.1, False),

    ("SpeicherTemp", 0x0804, 2, 0.1, False),
    ("SpeicherTemp_soll_akt", 0x6500, 2, 0.1, False),

    ("DeviceIdent", 0x00f8, 8, 'raw', False)
]


# Viessdata utils
write_viessdata_csv = True
viessdata_csv_path = ""
dec_separator = ","
