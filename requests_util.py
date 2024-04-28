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
import settings_ini


def get_valstr(data, frmat, signd:bool) -> str:
    scale = utils.to_number(frmat)
    if(scale is not None):
        return utils.bytesval(data, scale, signd)
    else:
        #TODO hier evtl weitere Formate umsetzen
        #return raw
        return utils.arr2hexstr(data)

def perform_bytebit_filter(data, item):
    # item is poll list entry:    (Name, DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)
    # may also be read request: ("read", DpAddr, Len, 'b:startbyte:lastbyte:bitmask:endian', Scale, Signed)

    bparts = item[3].split(':')

    bstart = int(bparts[1])
    bend = bstart
    if(len(bparts) > 1):
        bend = int(bparts[2])

    udata = data[bstart:(bend+1)]
 
    # first apply mask if given
    if(len(bparts) > 3):
        if(bparts[3] != ''):
            amask = utils.hexstr2arr(str(bparts[3]).replace('0x',''))
            for i in range(len(udata)+1):
                if(i > len(amask)):
                    break
                udata = udata & amask

    endian = 'little'    # € ['little, 'big', 'raw'] 
    if(len(bparts) > 4):
        if(bparts[4] != ''):
            endian = bparts[4]
    
    if(len(item) > 4):
        scal = item[4]
        if(scal == 'raw'):
            endian = 'raw'

    if(endian == 'raw'):
        return utils.arr2hexstr(udata)
    else:
        signd = False
        if(len(item) > 5):
            signd = utils.to_bool(str(item[5]))

        uvalue = int.from_bytes(udata, byteorder=endian, signed=signd)

        if((scal is not None) and (scal != 1)):
            uvalue = round(uvalue * scal, settings_ini.max_decimals)
        return uvalue


# 'main' functions +++++++++++++++++++++++++++++

# TCP, MQTT requests
def respond_to_request(request:str, serViDev) -> tuple[int, str]:   # retcode, string_to_pass 
    parts = request.split(';')
    numelms = len(parts)
    retstr = ''
    retcode = 0

    if(numelms == 1):
        # full raw +++++++++++++++++++ "4105000100F80806"
        bstr = bytes.fromhex(parts[0])
        serViDev.reset_input_buffer()
        serViDev.write(bstr)
        #print("sent to OL:", bbbstr(bstr))
        data = optolinkvs2.receive_fullraw(settings_ini.fullraw_eot_time,settings_ini.fullraw_timeout, serViDev)
        retstr = utils.arr2hexstr(data)
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
            retstr = str(retcode) + ';' + utils.arr2hexstr(data)

        elif(cmnd in ["read", "r"]):  # "read;0x0804;1;0.1;False"
            # read +++++++++++++++++++
            retcode, addr, data = optolinkvs2.read_datapoint_ext(utils.get_int(parts[1]), int(parts[2]), serViDev)
            if(retcode==1):
                if(numelms > 3):
                    if(str(parts[3]).startswith('b:')):
                        retstr = perform_bytebit_filter(data, parts)
                    else:
                        signd = False
                        if(numelms > 4):
                            signd = utils.to_bool(parts[4])
                        retstr = get_valstr(data, parts[3], signd)
                else:
                    #return raw
                    retstr = utils.arr2hexstr(data)
            elif(data):
                # probably error message
                retstr = int.from_bytes(data, 'big')
            else:
                retstr = "?"
            retstr = str(retcode) + ';' + str(addr) + ';' + str(retstr)

        elif(cmnd in ["write", "w"]):  # "write;0x6300;1;48"
            # write +++++++++++++++++++
            #raise Exception("write noch nicht fertig") #TODO scaling und so
            bval = utils.get_int(parts[3]).to_bytes(int(parts[2]), 'big')
            retcode, addr, data = optolinkvs2.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = int.from_bytes(bval, 'big')
            elif(data):
                # probably error message
                val = int.from_bytes(data, 'big')
            else:
                val = "?"
            retstr = str(retcode) + ';' + str(addr) + ';' + str(val)

        elif(cmnd in ["writeraw", "wraw"]):  # "writeraw;0x6300;2A"
            # write raw +++++++++++++++++++
            bval = utils.hexstr2arr(str(parts[2]).replace('0x',''))
            retcode, addr, data = optolinkvs2.write_datapoint_ext(utils.get_int(parts[1]), bval, serViDev)
            if(retcode == 1): 
                val = int.from_bytes(bval, 'big')
            elif(data):
                val = int.from_bytes(data, 'big')
            else:
                val = "?"
            retstr = str(retcode) + ';' + str(addr) + ';' + str(val)
        else:
            print("unknown command received:", cmnd)
    return retcode, retstr


