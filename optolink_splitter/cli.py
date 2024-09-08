from click import command, option
from optolink_splitter.optolinkvs2_switch import optolink_vs2_switch
from typing import Optional

@command()
@option('--optolink-port', required=True, type=str, default="/dev/ttyUSB0", show_default=True, help="Usually '/dev/ttyUSB0'")
@option('--vitoconnect-port', required=False, type=str, default=None, show_default=True, help="Usually '/dev/ttyS0'. On older Pis rather 'dev/ttyAMA0'. Does not have to be specified if no Vitoconnect is used.")
def main(vitoconnect_port: Optional[str]) -> None:
    print("Hello World")
    #optolink_vs2_switch()


if __name__ == "__main__":
    main()