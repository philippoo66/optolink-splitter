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

from typing import Any

from c_settings_adapter import settings
from logger_util import logger
import utils
import vs12_adapter
import onewire_util
import c_w1value



# onewire util
w1values: dict[int, c_w1value.W1Value] = {}

def init_w1_values_check():
    for addr,info in settings.w1sensors.items():  # Addr: ('<w1_folder/sn>', '<slave_type>')
        if info[1].lower() == 'ds18b20':
            # scalar value, check max_change
            w1val = c_w1value.W1Value(addr, max_change=10.0, max_ignore=3)
        else:
            # accept objects, no check
            w1val = c_w1value.W1Value(addr, max_change=-1)        
        # add to dict
        w1values[addr] = w1val


def get_value(data, frmat, signd:bool):
    scale = utils.to_number(frmat)
    if(scale is not None):
        return utils.bytesval(data, scale, signd)
    else:
        #TODO hier evtl weitere Formate umsetzen
        frmat = str(frmat)
        if(frmat == 'vdatetime'):
            return utils.vdatetime2str(data)
        elif(frmat == 'vcaldatetime'):
            return utils.vdatetime2str(data, 0)
        elif(frmat == 'unixtime'):
            return utils.unixtime2str(data)
        elif(frmat == 'utf8'):
            return utils.utf82str(data)
        elif(frmat == 'utf16'):
            return utils.utf162str(data)
        elif(frmat == 'bool'):
            return str(utils.bytesval(data) != 0)
        elif(frmat == 'boolinv'):
            return str(utils.bytesval(data) == 0)
        elif(frmat == 'onoff'):
            return 'ON' if(utils.bytesval(data) != 0) else 'OFF'
        elif(frmat == 'offon'):
            return 'ON' if(utils.bytesval(data) == 0) else 'OFF'
        elif(frmat == 'bin'):
            ffrmt = f"0{len(data)*8}b"
            return f"{utils.bytesval(data):{ffrmt}}"
        elif(frmat.startswith('f:')):
            ffrmt = frmat[2:]
            return f"{utils.bytesval(data):{ffrmt}}"
        else:
            #return raw
            return utils.arr2hexstr(data)

def perform_bytebit_filter(data, item):
    # item is poll list entry:  (Name, DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)
    # may also be read request: "read; DpAddr; Len; 'b:startbyte:lastbyte:bitmask:endian'; Scale; Signed"

    bparts = item[3].split(':')

    bstart = int(bparts[1])
    bend = bstart
    if(len(bparts) > 2):
        if(bparts[2] != ''):
            bend = int(bparts[2])

    udata = data[bstart:(bend+1)]
    dlen = bend - bstart + 1

    # first apply mask if given
    if(len(bparts) > 3):
        if(bparts[3] != ''):
            smask = str(bparts[3]).strip()
            imask = utils.get_int(smask)
            amask = bytearray(imask.to_bytes(dlen, 'big'))
            # now apply the mask byte for byte
            for i in range(dlen):
                udata[i] = udata[i] & amask[i]

    # evaluate endian if given
    if(len(bparts) > 4) and (bparts[4] == 'big'):
        # convert to int
        ival = int.from_bytes(udata, byteorder='big')
        # convert to bytearray to get evaluated in response_to_request()
        return bytearray(ival.to_bytes(dlen, byteorder='little'))
    else:  # also covers 'raw' for backward compatibility
        return udata
 
def perform_bytebit_filter_and_evaluate(data, parts):
    # parts: ['valname/read', addr, len, 'b:...', fact, signd]   min up to 'b:...'
    valdata = perform_bytebit_filter(data, parts)
    numelms = len(parts)
    if(numelms > 4):
        # factor is parts[4]
        # eval signed
        signd = False
        if(numelms > 5):
            signd = utils.get_bool(parts[5])
        # now get value 
        val = get_value(valdata, parts[4], signd)
    else:
        # return raw
        val = utils.arr2hexstr(valdata)
    return val


def get_retstr(retcode, addr, val) -> str:
    prefix = '' #'0x' if('x' in settings.retcode_format.lower()) else '' 
    sretcode = prefix + format(retcode, settings.retcode_format)
    prefix = '0x' if('x' in settings.resp_addr_format.lower()) else '' 
    saddr = prefix + format(addr, settings.resp_addr_format)
    return f"{sretcode};{saddr};{val}"


# 'main' functions +++++++++++++++++++++++++++++
def response_to_request(request, serViDev) -> tuple[int, bytearray, Any, str]:   # retcode, data, value, string_to_pass 
    # error handling in calling proc
    ispollitem = False
    if(isinstance(request, str)):
        # TCP, MQTT requests
        parts = request.split(';')
    else:
        # poll item
        ispollitem = True
        parts = request
    
    numelms = len(parts)
    data = bytearray()
    val = None
    retstr = ''
    retcode = 0

    if(numelms == 1):
        # full raw +++++++++++++++++++ "4105000100F80806"
        bstr = bytes.fromhex(parts[0].replace(' ',''))
        serViDev.reset_input_buffer()
        serViDev.write(bstr)
        #print("sent to OL:", utils.bbbstr(bstr))  #temp
        retcode, data = vs12_adapter.receive_fullraw(settings.fullraw_eot_time, settings.fullraw_timeout, serViDev)
        val = utils.arr2hexstr(data)
        retstr = str(val)
        #print(f"recd fr OL: {utils.bbbstr(data)}, retcode {retcode:02x}") #temp

    elif(numelms > 1):
        cmnd = parts[0].lower()
        if(cmnd == "raw"):  # "raw;4105000100F80806"
            # raw +++++++++++++++++++
            bstr = bytes.fromhex(parts[1].replace(' ',''))
            serViDev.reset_input_buffer()
            serViDev.write(bstr)
            #print("sent to OL:", bbbstr(retstr))
            retcode, _, data = vs12_adapter.receive_telegr(True, True, serViDev)
            #print(f"recd fr OL: {utils.bbbstr(data)}, retcode {retcode:02x}") #temp
            val = utils.arr2hexstr(data)
            retstr = f"{retcode};{val}"
            #data = bytearray()

        elif((cmnd in ["read", "r"]) or ispollitem):  # "read;0x0804;1;0.1;False" or "r;0x2500;22;'b:0:1';0.1"
            # read +++++++++++++++++++
            addr = utils.get_int(parts[1])
            if(addr in settings.w1sensors):
                # 1wire sensor
                retcode, val = onewire_util.read_w1sensor(addr)
                val = w1values[addr].checked(val)
            else:
                # Optolink item
                retcode, addr, data = vs12_adapter.read_datapoint_ext(addr, int(parts[2]), serViDev)
                if(retcode==1):
                    if(numelms > 3):
                        if(str(parts[3]).startswith('b:')):
                            # parts: ['valname/read', addr, len, 'b:...', fact, signd]
                            val = perform_bytebit_filter_and_evaluate(data, parts)
                        else:
                            # factor is parts[3]
                            # eval signed
                            signd = False
                            if(numelms > 4):
                                signd = utils.get_bool(parts[4])
                            # now get value 
                            val = get_value(data, parts[3], signd)
                    else:
                        # return raw
                        val = utils.arr2hexstr(data)
                elif(data):
                    # probably error message
                    val = utils.arr2hexstr(data)  #f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
                else:
                    val = "?"
            retstr = get_retstr(retcode, addr, val)

        elif(cmnd in ["write", "w"]):  # "write;0x6300;1;48"
            # write +++++++++++++++++++
            #raise Exception("write noch nicht fertig") #TODO scaling und so
            ival = utils.get_int(parts[3])
            bval = ival.to_bytes(int(parts[2]), 'little', signed=(ival < 0))
            retcode, addr, data = vs12_adapter.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = int.from_bytes(bval, 'little', signed=(ival < 0))
            elif(data):
                # probably error message
                val = utils.arr2hexstr(data)  #f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(retcode, addr, val)

        elif(cmnd in ["writeraw", "wraw"]):  # "writeraw;0x27d4;2A"
            # write raw +++++++++++++++++++
            hexstr = str(parts[2]).replace('0x','').replace(' ','')
            bval = utils.hexstr2arr(hexstr)
            retcode, addr, data = vs12_adapter.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = hexstr   #int.from_bytes(bval, 'big')
            elif(data):
                # probably error message
                val = utils.arr2hexstr(data)  #f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(retcode, addr, val)
        
        elif(cmnd in ["request", "req"]):  # "request;<i_fctcode>;<i_addr>;<i_len>;<s_data>;<i_protid>"
            fctcode = utils.get_int(parts[1])
            addr = utils.get_int(parts[2])
            rlen = utils.get_int(parts[3])
            bstr = bytes.fromhex(parts[4].replace('0x','').replace(' ','')) if (numelms > 4) else bytes()
            protid = utils.get_int(parts[5]) if (numelms > 5) else 0x00
            # request
            retcode, addr, data = vs12_adapter.do_request(serViDev, fctcode, addr, rlen, bstr, protid)
            # eval response
            val = utils.arr2hexstr(data) if data else "none"
            retstr = get_retstr(retcode, addr, val)

        else:
            retstr = f"unknown command received: {cmnd}"
            logger.warning(retstr)
    # and finally return...
    return retcode, data, val, retstr

