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

import utils
import optolinkvs2
import onewire_util
import settings_ini


def get_value(data, frmat, signd:bool) -> any:
    scale = utils.to_number(frmat)
    if(scale is not None):
        return utils.bytesval(data, scale, signd)
    else:
        #TODO hier evtl weitere Formate umsetzen
        if(frmat == 'vdatetime'):
            return utils.vdatetime2str(data)
        elif(frmat == 'unixtime'):
            return utils.unixtime2str(data)
        elif(frmat == 'utf8'):
            return utils.utf82str(data)
        else:
            #return raw
            return utils.arr2hexstr(data)

def perform_bytebit_filter(data, item):
    # item is poll list entry:  (Name, DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)
    # may also be read request: "read; DpAddr; Len; b:startbyte:lastbyte:bitmask:endian; Scale; Signed"

    bparts = item[3].split(':')

    bstart = int(bparts[1])
    bend = bstart
    if(len(bparts) > 1):
        if(bparts[2] != ''):
            bend = int(bparts[2])

    udata = data[bstart:(bend+1)]
 
    # first apply mask if given
    if(len(bparts) > 3):
        if(bparts[3] != ''):
            smask = str(bparts[3]).strip()
            imask = utils.get_int(smask)
            dlen = bend - bstart + 1
            amask = bytearray(imask.to_bytes(dlen, 'big'))
            # now apply the mask byte for byte
            for i in range(dlen):
                udata[i] = udata[i] & amask[i]

    endian = 'little'    # € ['little, 'big', 'raw'] 
    if(len(bparts) > 4):
        if(bparts[4] != ''):
            endian = bparts[4]
    
    scal = None
    if(len(item) > 4):
        if(item[4] != 'raw'):  # only for backward compatibility
            scal = float(item[4])

    if(scal is None) or (endian == 'raw'):  # backward compatibility
        return utils.arr2hexstr(udata)
    else:
        signd = False
        if(len(item) > 5):
            signd = utils.get_bool(item[5])

        uvalue = int.from_bytes(udata, byteorder=endian, signed=signd)

        if(scal != 1.0):
            uvalue = round(uvalue * scal, int(settings_ini.max_decimals))

        return uvalue


def get_retstr(retcode, addr, val) -> str:
    prefix = ''
    if('x' in settings_ini.resp_addr_format.lower()):
        prefix = '0x'
    saddr = prefix + format(addr, settings_ini.resp_addr_format)
    #retstr = str(retcode) + ';' + str(addr) + ';' + str(val)
    return f"{retcode};{saddr};{val}"


# 'main' functions +++++++++++++++++++++++++++++
def response_to_request(request, serViDev) -> tuple[int, bytearray, any, str]:   # retcode, data, value, string_to_pass 
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
        bstr = bytes.fromhex(parts[0])
        serViDev.reset_input_buffer()
        serViDev.write(bstr)
        #print("sent to OL:", bbbstr(bstr))
        data = optolinkvs2.receive_fullraw(settings_ini.fullraw_eot_time,settings_ini.fullraw_timeout, serViDev)
        val = utils.arr2hexstr(data)
        retstr = str(val)
        retcode = 0x01  # attention!
        #print("recd fr OL:", bbbstr(data))

    elif(numelms > 1):
        cmnd = parts[0].lower()
        if(cmnd == "raw"):  # "raw;4105000100F80806"
            # raw +++++++++++++++++++
            bstr = bytes.fromhex(parts[1])
            serViDev.reset_input_buffer()
            serViDev.write(bstr)
            #print("sent to OL:", bbbstr(retstr))
            retcode, _, data = optolinkvs2.receive_vs2telegr(True, True, serViDev)
            #print("recd fr OL:", ret, ',', bbbstr(data))
            val = utils.arr2hexstr(data)
            retstr = f"{retcode};{val}"
            data = bytearray()

        elif((cmnd in ["read", "r"]) or ispollitem):  # "read;0x0804;1;0.1;False" or "r;0x2500;22;'b:0:1';0.1"
            # read +++++++++++++++++++
            addr = utils.get_int(parts[1])
            if(addr in settings_ini.w1sensors): 
                # 1wire sensor
                retcode, val = onewire_util.read_w1sensor(addr)
            else:
                # Optolink item
                retcode, addr, data = optolinkvs2.read_datapoint_ext(addr, int(parts[2]), serViDev)
                if(retcode==1):
                    if(numelms > 3):
                        if(str(parts[3]).startswith('b:')):
                            #print(f"H perform_bytebit_filter, ispollitem {ispollitem}")
                            val = perform_bytebit_filter(data, parts)
                        else:
                            signd = False
                            if(numelms > 4):
                                signd = utils.get_bool(parts[4])
                            val = get_value(data, parts[3], signd)
                    else:
                        #return raw
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
            bval = (utils.get_int(parts[3])).to_bytes(int(parts[2]), 'little')
            retcode, addr, data = optolinkvs2.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = int.from_bytes(bval, 'little')
            elif(data):
                # probably error message
                val = utils.arr2hexstr(data)  #f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(retcode, addr, val)

        elif(cmnd in ["writeraw", "wraw"]):  # "writeraw;0x6300;2A"
            # write raw +++++++++++++++++++
            hexstr = str(parts[2]).replace('0x','')
            bval = utils.hexstr2arr(hexstr)
            retcode, addr, data = optolinkvs2.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = hexstr   #int.from_bytes(bval, 'big')
            elif(data):
                # probably error message
                val = utils.arr2hexstr(data)  #f"{int.from_bytes(data, 'little')} ({utils.bbbstr(data)})"
            else:
                val = "?"
            retstr = get_retstr(retcode, addr, val)
        else:
            print("unknown command received:", cmnd)
    # and finally return...
    return retcode, data, val, retstr

