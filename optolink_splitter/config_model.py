from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class SplitterConfig:
    optolink_port: str
    poll_items_config_path: str
    poll_interval: int
    vitoconnect_port: Optional[str]
    vitoconnect_vs2timeout: Union[int, float]
    mqtt_address: Optional[str]
    mqtt_user: Optional[str]
    mqtt_topic: str
    mqtt_fstr: str
    mqtt_listen_address: Optional[str]
    mqtt_respond_address: str
    tcpip_port: Optional[int]
    fullraw_eot_time: Union[int, float]
    fullraw_timeout: Union[int, float]
    logging_vitoconnect_log_path: Optional[str]
    logging_show_opto_rx: bool
    format_max_decimals: int
    format_data_hex_format: str
    format_resp_addr_format: str
    viessdata_csv_path: Optional[str]
    viessdata_csv_delimiter: str
    viessdata_csv_buffer_to_write: int
    w1sensors_config_path: str
