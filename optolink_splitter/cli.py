from click import command, option
from optolink_splitter.optolinkvs2_switch import optolink_vs2_switch
from typing import Optional

@command()
@option('--optolink-port', required=True, type=str, default="/dev/ttyUSB0", show_default=True, help="Usually '/dev/ttyUSB0'.")
@option('--vitoconnect-port', required=False, type=str, default=None, show_default=True, help="Usually '/dev/ttyS0'. On older Pis rather 'dev/ttyAMA0'. Does not have to be specified if no Vitoconnect is used.")
@option('--vitoconnect-vs2timeout', required=False, type=int, default=120, show_default=True, help="Seconds to detect VS2 protocol on vitoconnect connection.")
@option('--mqtt-address', required=False, type=str, default=None, show_default=True, help="IP Address for mqtt Server, e.g. '192.168.0.123'. Does not have to be specified if mqtt is not used.")
def main(optolink_port: str, 
         vitoconnect_port: Optional[str], 
         vitoconnect_vs2timeout: int, 
         mqtt_address: Optional[str], 
         ) -> None:
    print("Hello World")
    #optolink_vs2_switch()


if __name__ == "__main__":
    main()