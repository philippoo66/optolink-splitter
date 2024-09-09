from click import command, option
from optolink_splitter.optolinkvs2_switch import optolink_vs2_switch
from optolink_splitter.config_model import SplitterConfig
from typing import Union


def add_options(f):
    """Decorator to add cli options."""
    options = [
        option(
            "--optolink-port",
            required=True,
            type=str,
            default="/dev/ttyUSB0",
            show_default=True,
            help="Usually '/dev/ttyUSB0'.",
        ),
        option(
            "--poll-items-config-path",
            required=True,
            type=str,
            default=None,
            show_default=True,
            help="Path to get poll items config '/path/to/log/config.csv'. The header in the csv file must contain 'name,dpaddr,len,scale,signed' column names.",
        ),
        option(
            "--poll-interval",
            required=False,
            type=int,
            default=30,
            show_default=True,
            help="Poll interval in seconds. Set to '0' for continuous polling. Set to '-1' to disable polling.",
        ),
        option(
            "--vitoconnect-port",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="Usually '/dev/ttyS0'. On older Pis rather 'dev/ttyAMA0'. Does not have to be specified if no Vitoconnect is used.",
        ),
        option(
            "--vitoconnect-vs2timeout",
            required=False,
            type=Union[int, float],
            default=120,
            show_default=True,
            help="Seconds to detect VS2 protocol on vitoconnect connection.",
        ),
        option(
            "--mqtt-address",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="IP address with port number for mqtt Server, e.g. '192.168.0.123:1883'. Does not have to be specified if mqtt is not used.",
        ),
        option(
            "--mqtt-user",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="Username and password for mqtt server, e.g. 'user:password'. Does not have to be specified if not required by mqtt server.",
        ),
        option(
            "--mqtt-topic",
            required=False,
            type=str,
            default="optolink",
            show_default=True,
            help="Mqtt topic which should be used.",
        ),
        option(
            "--mqtt-fstr",
            required=False,
            type=str,
            default="{dpname}",
            show_default=True,
            help="Mqtt fstr which should be used.",
        ),
        option(
            "--mqtt-listen-address",
            required=False,
            type=str,
            default="optolink/cmnd",
            show_default=True,
            help="Mqtt listen address. If it is set to 'None', listen is deactivated.",
        ),
        option(
            "--mqtt-respond-address",
            required=False,
            type=str,
            default="optolink/resp",
            show_default=True,
            help="Mqtt respond address.",
        ),
        option(
            "--tcpip-port",
            required=False,
            type=int,
            default=None,
            show_default=True,
            help="TCP/IP Port which should be used for Viessdata connections (default: '65234'). Does not have to be specified if no Viessdata is required.",
        ),
        option(
            "--fullraw-eot-time",
            required=False,
            type=Union[int, float],
            default=0.05,
            show_default=True,
            help="Amount of time in seconds to decide end of telegram.",
        ),
        option(
            "--fullraw-timeout",
            required=False,
            type=Union[int, float],
            default=2,
            show_default=True,
            help="Amount of time in seconds for timeout to return in any case.",
        ),
        option(
            "--logging-vitoconnect-log-path",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="Path to logfile for logging communication with Vitoconnect (rx+tx telegrams). E.g '/path/to/log/file.txt'. Only have to be specified to activate logging.",
        ),
        option(
            "--logging-show-opto-rx",
            required=False,
            type=bool,
            default=True,
            show_default=True,
            help="Display rx messages on screen (No output when ran as service).",
        ),
        option(
            "--format-max-decimals",
            required=False,
            type=int,
            default=4,
            show_default=True,
            help="Maximum amount of decimals to show.",
        ),
        option(
            "--format-data-hex-format",
            required=False,
            type=str,
            default="02x",
            show_default=True,
            help="Set to '02X' to get capitals in hex format.",
        ),
        option(
            "--format-resp-addr-format",
            required=False,
            type=str,
            default="d",
            show_default=True,
            help="Format of DP address in MQTT/TCPIP request response. E.g. 'd': decimal, '04X': hex 4 digits.",
        ),
        option(
            "--viessdata-csv-path",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="Path to write viessdata .csv file. E.g '/path/to/log/file.csv'. Only have to be specified to generate viessdata .csv.",
        ),
        option(
            "--viessdata-csv-delimiter",
            required=False,
            type=str,
            default=",",
            show_default=True,
            help="Delimiter to use for viessdata .csv.",
        ),
        option(
            "--viessdata-csv-buffer-to-write",
            required=False,
            type=int,
            default=60,
            show_default=True,
            help="Amount of time to buffer before write to viessdata .csv.",
        ),
        option(
            "--w1sensors-config-path",
            required=False,
            type=str,
            default=None,
            show_default=True,
            help="Path to get wisensors config '/path/to/log/config.csv'. Only have to be specified to activate wisensors.",
        ),
    ]
    for opt in reversed(options):
        f = opt(f)
    return f


@command()
@add_options
def main(**kwargs):
    config = SplitterConfig(**kwargs)
    optolink_vs2_switch(config)


if __name__ == "__main__":
    main()
