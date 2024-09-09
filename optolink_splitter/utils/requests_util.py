"""
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
"""

from typing import Any

from optolink_splitter.config_model import SplitterConfig
from optolink_splitter.optolinkvs2 import (
    receive_fullraw,
    receive_vs2telegr,
    read_datapoint_ext,
    write_datapoint_ext,
)
from optolink_splitter.utils.common_utils import (
    vdatetime2str,
    utf82str,
    to_number,
    bytesval,
    arr2hexstr,
    get_bool,
    hexstr2arr,
    get_int,
)
from optolink_splitter.utils.onewire_util import read_w1sensor


def get_value(data, frmat, signd: bool) -> Any:
    scale = to_number(frmat)
    if scale is not None:
        return bytesval(data, scale, signd)
    else:
        # TODO hier evtl weitere Formate umsetzen
        if frmat == "vdatetime":
            return vdatetime2str(data)
        elif frmat == "utf8":
            return utf82str(data)
        else:
            # return raw
            return arr2hexstr(data)


def perform_bytebit_filter(config: SplitterConfig, data, item):
    # item is poll list entry:    (Name, DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)
    # may also be read request: ("read", DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)

    bparts = item[3].split(":")

    bstart = int(bparts[1])
    bend = bstart
    if len(bparts) > 1:
        if bparts[2] != "":
            bend = int(bparts[2])

    udata = data[bstart : (bend + 1)]

    # first apply mask if given
    if len(bparts) > 3:
        if bparts[3] != "":
            amask = hexstr2arr(str(bparts[3]).replace("0x", ""))
            for i in range(len(udata) + 1):
                if i > len(amask):
                    break
                udata = udata & amask

    endian = "little"  # € ['little, 'big', 'raw']
    if len(bparts) > 4:
        if bparts[4] != "":
            endian = bparts[4]

    if len(item) > 4:
        scal = item[4]
        if scal == "raw":
            endian = "raw"

    if endian == "raw":
        return arr2hexstr(udata, config.format_data_hex_format)
    else:
        signd = False
        if len(item) > 5:
            signd = get_bool(item[5])

        uvalue = int.from_bytes(udata, byteorder=endian, signed=signd)

        if (scal is not None) and (scal != 1):
            uvalue = round(uvalue * scal, config.format_max_decimals)
        return uvalue


def get_retstr(config: SplitterConfig, retcode, addr, val) -> str:
    prefix = ""
    if "x" in config.format_resp_addr_format.lower():
        prefix = "0x"
    saddr = prefix + format(addr, config.format_resp_addr_format)
    # retstr = str(retcode) + ';' + str(addr) + ';' + str(val)
    return f"{retcode};{saddr};{val}"


# 'main' functions +++++++++++++++++++++++++++++
def response_to_request(
    config: SplitterConfig, w1sensors: list[tuple], request, serViDev
) -> tuple[int, bytearray, Any, str]:  # retcode, data, value, string_to_pass
    ispollitem = False
    if isinstance(request, str):
        # TCP, MQTT requests
        parts = request.split(";")
    else:
        # poll item
        ispollitem = True
        parts = request

    numelms = len(parts)
    data = bytearray()
    val = None
    retstr = ""
    retcode = 0

    if numelms == 1:
        # full raw +++++++++++++++++++ "4105000100F80806"
        bstr = bytes.fromhex(parts[0])
        serViDev.reset_input_buffer()
        serViDev.write(bstr)
        # print("sent to OL:", bbbstr(bstr))
        data = receive_fullraw(
            config, config.fullraw_eot_time, config.fullraw_timeout, serViDev
        )
        val = arr2hexstr(data, config.format_data_hex_format)
        retstr = str(val)
        retcode = 0x01  # attention!
        # print("recd fr OL:", bbbstr(data))

    elif numelms > 1:
        cmnd = parts[0].lower()
        if cmnd == "raw":  # "raw;4105000100F80806"
            # raw +++++++++++++++++++
            bstr = bytes.fromhex(parts[1])
            serViDev.reset_input_buffer()
            serViDev.write(bstr)
            # print("sent to OL:", bbbstr(retstr))
            retcode, _, data = receive_vs2telegr(
                config.format_data_hex_format,
                config.logging_show_opto_rx,
                True,
                True,
                serViDev,
            )
            # print("recd fr OL:", ret, ',', bbbstr(data))
            val = arr2hexstr(data, config.format_data_hex_format)
            retstr = f"{retcode};{val}"
            data = bytearray()

        elif (cmnd in ["read", "r"]) or ispollitem:  # "read;0x0804;1;0.1;False"
            # read +++++++++++++++++++
            addr = get_int(parts[1])
            if any(addr in item for item in w1sensors):
                # 1wire sensor
                retcode, val = read_w1sensor(
                    addr, w1sensors, config.logging_show_opto_rx
                )
            else:
                # Optolink item
                retcode, addr, data = read_datapoint_ext(addr, int(parts[2]), serViDev)
                if retcode == 1:
                    if numelms > 3:
                        if str(parts[3]).startswith("b:"):
                            val = perform_bytebit_filter(config, data, parts)
                        else:
                            signd = False
                            if numelms > 4:
                                signd = get_bool(parts[4])
                            val = get_value(data, parts[3], signd)
                    else:
                        # return raw
                        val = arr2hexstr(data, config.format_data_hex_format)
                elif data:
                    # probably error message
                    val = arr2hexstr(
                        data, config.format_data_hex_format
                    )  # f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
                else:
                    val = "?"
            retstr = get_retstr(config, retcode, addr, val)

        elif cmnd in ["write", "w"]:  # "write;0x6300;1;48"
            # write +++++++++++++++++++
            # raise Exception("write noch nicht fertig") #TODO scaling und so
            bval = (get_int(parts[3])).to_bytes(int(parts[2]), "little")
            retcode, addr, data = write_datapoint_ext(get_int(parts[1]), bval, serViDev)
            if retcode == 1:
                val = int.from_bytes(bval, "little")
            elif data:
                # probably error message
                val = arr2hexstr(
                    data, config.format_data_hex_format
                )  # f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(config, retcode, addr, val)

        elif cmnd in ["writeraw", "wraw"]:  # "writeraw;0x6300;2A"
            # write raw +++++++++++++++++++
            hexstr = str(parts[2]).replace("0x", "")
            bval = hexstr2arr(hexstr)
            retcode, addr, data = write_datapoint_ext(get_int(parts[1]), bval, serViDev)
            if retcode == 1:
                val = hexstr  # int.from_bytes(bval, 'big')
            elif data:
                # probably error message
                val = arr2hexstr(
                    data, config.format_data_hex_format
                )  # f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(config, retcode, addr, val)
        else:
            print("unknown command received:", cmnd)
    # and finally return...
    return retcode, data, val, retstr
