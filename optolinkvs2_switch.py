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

version = "1.7.1.3"

import serial
import time
import threading
import importlib
import json
import signal

from logger_util import logger
import settings_ini
import optolinkvs2
import viconn_util
import viessdata_util
import c_tcpserver
import requests_util
import c_logging
from c_polllist import poll_list
import utils
import wo1c_energy

# exit flag e.g. to stop endless loops
progr_exit_flag = False

# ether objects
mod_mqtt_util = None
tcp_server = None

# Threading-Events zur Steuerung des Neustarts
restart_event = threading.Event()
#shutdown_event = threading.Event()


def olbreath(retcode:int):
    """
    give vitotrol some time after comm to do other things
    """
    if(retcode <= 0x03):
        # success, err msg
        time.sleep(settings_ini.olbreath)
    elif(retcode in [0xFF, 0xAA, 0xAB]):
        # timeout, err_handle, final item skipped in cycle
        pass
    else:
        # allow calming down
        time.sleep(5 * settings_ini.olbreath)


# polling list +++++++++++++++++++++++++++++
poll_pointer = 0
poll_cycle = 0

def do_poll_item(poll_data, ser:serial.Serial, mod_mqtt=None) -> int:  # retcode
    global poll_pointer
    val = "?"
    item = "?"

    try:
        # loop though poll items until find one to be done this cycle
        while(True):  
            # handle PollCycle option +++++++++++++++++++++++
            item = poll_list.items[poll_pointer]  # ([PollCycle,] Name, DpAddr, Len, Scale/Type, Signed)
            if(len(item) > 1 and isinstance(item[0], int)):
                if(item[0] != 0) and (poll_cycle % item[0] != 0):
                    # +++ do not poll this item this time +++

                    # leave poll_data[poll_pointer] unchanged

                    poll_pointer += 1
                    if(poll_pointer == poll_list.num_items):
                        # no further item this cycle                    
                        return 0xAB
                else:
                    # remove PollCycle for further processing
                    item = item[1:]
                    break
            else:
                break

        retcode, data, val, _ = requests_util.response_to_request(item, ser)

        if(retcode == 0x01):
            # save val in buffer for csv
            poll_data[poll_pointer] = val

            # post to MQTT broker
            if(mod_mqtt is not None): 
                mod_mqtt.publish_read(item[0], item[1], val)

            # probably more bytebit values of the same datapoint?!
            if(len(item) > 3):
                if(str(item[3]).lower().startswith('b:')):
                    # bytebit filter +++++++++
                    while((poll_pointer + 1) < poll_list.num_items):
                        next_idx = poll_pointer + 1
                        next_item = poll_list.items[next_idx]

                        # remove PollCycle in case
                        if(isinstance(item[0], int)):
                            next_item = next_item[1:]
                        
                        # if next address same AND next len same AND next type starts with 'b:'
                        if((len(next_item) > 3) and (next_item[1] == item[1]) and (next_item[2] == item[2]) and (str(next_item[3]).lower()).startswith('b:')):
                            next_val = requests_util.perform_bytebit_filter_and_evaluate(data, next_item)

                            # save val in buffer for csv
                            poll_data[next_idx] = next_val

                            if(mod_mqtt is not None): 
                                # publish to MQTT broker
                                mod_mqtt.publish_read(next_item[0], next_item[1], next_val)

                            poll_pointer = next_idx
                        else:
                            break
        else:
            logger.error(f"OL Error do_poll_item {poll_pointer}, Addr {item[1]:04X}, RetCode {retcode}, Data {val}")
        return retcode
    except Exception as e:
        logger.error(f"Error do_poll_item {poll_pointer}, {item}: {e}")
        raise


# poll timer    
def on_polltimer():
    global poll_pointer
    if(poll_pointer > poll_list.num_items):
        poll_pointer = 0
    startPollTimer(settings_ini.poll_interval)

timer_pollinterval = threading.Timer(1.0, on_polltimer)

def startPollTimer(secs:float):
    global timer_pollinterval
    timer_pollinterval.cancel()
    timer_pollinterval = threading.Timer(secs, on_polltimer)
    timer_pollinterval.start()


# Vicon listener +++++++++++++++++++++++++++++
def vicon_thread_func(serViCon, serViDev):
    """
    Thread to receive Vitoconnect requests
    """
    print("running Vitoconnect listener")
    try:
        callback = mqtt_publ_viconn if settings_ini.viconn_to_mqtt else None
        viconn_util.exit_flag = False
        viconn_util.listen_to_Vitoconnect(serViCon, callback)
    except Exception as e:
        msg = f"Error in listen_to_Vitoconnect: {e}"
        c_logging.viconnlog.do_log(msg)
        logger.error(msg, "re-init")
        mqtt_publ_debug(msg)
        viconn_util.exit_flag = True
        restart_event.set()  # Hauptprogramm signalisiert, dass ein Neustart nötig ist
        return  # Thread wird beendet


# TCP loop +++++++++++++++++++++++++++++
def tcp_connection_loop():
    global tcp_server
    while(not progr_exit_flag):
        tcp_server = c_tcpserver.TcpServer("0.0.0.0", settings_ini.tcpip_port) #, verbose=True)
        tcp_server.run()
        tcp_server = None
        if progr_exit_flag: return
        #logger.info("TCP session closed, restart soon...")
        time.sleep(1)


# utils +++++++++++++++++++++++++++++
def do_special_command(cmnd:str) -> bool:

    if cmnd in ("exit", "exittcp", "closetcp", "resettcp"):
        if tcp_server:
            tcp_server.stop()
    elif cmnd in ("flushcsv"):
        if settings_ini.write_viessdata_csv:
            viessdata_util.buffer_csv_line([], True)
    elif cmnd in ('reset', 'resetrecent'):
        if(mod_mqtt_util is not None):
            mod_mqtt_util.reset_recent = True
    else:
        return False
    return True

def mqtt_publ_debug(msg:str):
    if(mod_mqtt_util is not None) and mod_mqtt_util.mqtt_client.is_connected:
        mod_mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/debug", msg)  


def mqtt_publ_viconn(retcd, addr, data, msgid, msqn, fctcd, dlen):
    if(mod_mqtt_util is not None) and mod_mqtt_util.mqtt_client.is_connected:
        if addr:
            topic = settings_ini.mqtt_topic + f"/viconn/{addr:04X}/{get_msgid(msgid)}"
            jdata = {"retcode" : get_retcode(retcd),
                    "fctcode" : get_fctcode(fctcd),
                    "datalen" : dlen,
                    "data" : f"0x{utils.arr2hexstr(data)}" if data else "none"}
            mod_mqtt_util.publish_smart(topic, json.dumps(jdata))

def get_msgid(val):
    if(val == 0): return "Vicon"
    elif(val in (1, 3)): return "Opto"
    else: return f"0x{val:02X}"

def get_retcode(val):
    strg = dicRetCodes.get(val) 
    if strg: return strg
    else: return f"0x{val:02X}"

def get_fctcode(val):
    strg = dicFunctionCodes.get(val) 
    if strg: return strg
    else: return f"{val}"

dicRetCodes = {
    0x01 : "success", 
    0x03 : "ErrMsg", 
    0x15 : "NACK", 
    0x20 : "UnknB0_Err", 
    0x41 : "STX_Err", 
    0xAA : "HandleLost", 
    0xFD : "PlLen_Err", 
    0xFE : "CRC_Err", 
    0xFF : "TimeOut"
}

dicFunctionCodes = {
    0 : "undefined",
    1 : "Virtual_READ",
    2 : "Virtual_WRITE",
    3 : "Physical_READ",
    4 : "Physical_WRITE",
    5 : "EEPROM_READ",
    6 : "EEPROM_WRITE",
    7 : "Remote_Procedure_Call",
    # 5 bits!?
    # 33 : "Virtual_MBUS",
    # 34 : "Virtual_MarktManager_READ",
    # 35 : "Virtual_MarktManager_WRITE",
    # 36 : "Virtual_WILO_READ",
    # 37 : "Virtual_WILO_WRITE",
    # 49 : "XRAM_READ",
    # 50 : "XRAM_WRITE",
    # 51 : "Port_READ",
    # 52 : "Port_WRITE",
    # 53 : "BE_READ",
    # 54 : "BE_WRITE",
    # 65 : "KMBUS_RAM_READ",
    # 67 : "KMBUS_EEPROM_READ",
    # 81 : "KBUS_DATAELEMENT_READ",
    # 82 : "KBUS_DATAELEMENT_WRITE",
    # 83 : "KBUS_DATABLOCK_READ",
    # 84 : "KBUS_DATABLOCK_WRITE",
    # 85 : "KBUS_TRANSPARENT_READ",
    # 86 : "KBUS_TRANSPARENT_WRITE",
    # 87 : "KBUS_INITIALISATION_READ",
    # 88 : "KBUS_INITIALISATION_WRITE",
    # 89 : "KBUS_EEPROM_LT_READ",
    # 90 : "KBUS_EEPROM_LT_WRITE",
    # 91 : "KBUS_CONTROL_WRITE",
    # 93 : "KBUS_MEMBERLIST_READ",
    # 94 : "KBUS_MEMBERLIST_WRITE",
    # 95 : "KBUS_VIRTUAL_READ",
    # 96 : "KBUS_VIRTUAL_WRITE",
    # 97 : "KBUS_DIRECT_READ",
    # 98 : "KBUS_DIRECT_WRITE",
    # 99 : "KBUS_INDIRECT_READ",
    # 100 : "KBUS_INDIRECT_WRITE",
    # 101 : "KBUS_GATEWAY_READ",
    # 102 : "KBUS_GATEWAY_WRITE",
    # 120 : "PROZESS_WRITE",
    # 123 : "PROZESS_READ",
    # 180 : "OT_Physical_Read",
    # 181 : "OT_Virtual_Read",
    # 182 : "OT_Physical_Write",
    # 183 : "OT_Virtual_Write",
    # 201 : "GFA_READ",
    # 202 : "GFA_WRITE",
}


# signal handling
def handle_exit(sig, frame):
    logger.info(f"received signal {sig}")
    raise(SystemExit)


# ------------------------
# Main
# ------------------------
def main():
    global mod_mqtt_util
    global poll_pointer, poll_cycle
    global progr_exit_flag

    # Signale abfangen für sauberes Beenden
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)


    # #temp!!
    # optolinkvs2.temp_callback = publish_viconn

    excptn = None

    logger.info(f"Version {version}")

    try:
    #if True:
        poll_list.make_list()
        # buffer for read data for writing viessdata.csv 
        poll_data = [None] * poll_list.num_items

        # serielle Verbidungen mit Vitoconnect und dem Optolink Kopf aufbauen ++++++++++++++
        serViDev = None  # Viessmann Device (Slave)
        serViCon = None  # Vitoconnect (Master)

        if(settings_ini.port_optolink is not None):
            serViDev = serial.Serial(settings_ini.port_optolink,
                        baudrate=4800,
                        parity=serial.PARITY_EVEN,
                        stopbits=serial.STOPBITS_TWO,
                        bytesize=serial.EIGHTBITS,
                        exclusive=True,
                        timeout=0)
        else:
            raise Exception("Error: Optolink device is mandatory!")

        if(settings_ini.port_vitoconnect is not None):
            serViCon = serial.Serial(settings_ini.port_vitoconnect,
                        baudrate=4800,
                        parity=serial.PARITY_EVEN,
                        stopbits=serial.STOPBITS_TWO,
                        bytesize=serial.EIGHTBITS,
                        exclusive=True,
                        timeout=0)

        # Empfangstask der sekundären Master starten (TcpIp, MQTT) ++++++++++++++

        # MQTT --------
        if(settings_ini.mqtt is not None):
            # avoid paho.mqtt required if not used
            mod_mqtt_util = importlib.import_module("mqtt_util")
            mod_mqtt_util.connect_mqtt()


        # TCP/IP connection --------
        if(settings_ini.tcpip_port is not None):
            tcp_thread = threading.Thread(target=tcp_connection_loop, daemon=True)
            tcp_thread.start()


        # some inits ++++++++++++++

        # one wire value check init
        requests_util.init_w1_values_check()

        # publish viconn or not
        vicon_publ_callback = mqtt_publ_viconn if settings_ini.viconn_to_mqtt else None


        # ------------------------
        # connection / re-connect loop
        # ------------------------        
        while(True):  #not shutdown_event.is_set():
            # run VS2 connection ------------------
            if(serViCon is not None):
                # reset vicon_request buffer
                viconn_util.vicon_request = bytearray()

                # Vitoconncet logging
                if(settings_ini.log_vitoconnect):
                    if(c_logging.viconnlog.log_handle is None):
                        c_logging.viconnlog.open_log()

                # detect/init VS2 Protokol ++++++++++++
                logger.info("awaiting VS2...")
                if not viconn_util.detect_vs2(serViCon, serViDev, settings_ini.vs2timeout):
                    raise Exception("VS2 protocol not detected within timeout")
                c_logging.viconnlog.do_log("VS2 protocol detected")           
                logger.info("VS2 detected")

                # listen to vicon ++++++++++++
                # run reception thread
                restart_event.clear()
                vicon_thread = threading.Thread(target=vicon_thread_func, args=(serViCon, serViDev), daemon=True)
                vicon_thread.start()

            else:
                # VS2 Protokoll am Slave initialisieren
                if(not optolinkvs2.init_vs2(serViDev)):
                    #logger.error("init_vs2 failed")
                    raise Exception("init_vs2 failed")  # schlecht für KW Protokoll
                logger.info("VS2 initialized")


            # Polling Mechanismus --------
            if(settings_ini.poll_interval > 0) and (poll_list.num_items > 0):
                startPollTimer(settings_ini.poll_interval)

            # ------------------------
            # Main Loop starten und Sachen abarbeiten ++++++++++++
            # ------------------------
            logger.info("enter main loop")
            num_tasks = 3
            request_pointer = 0
            #tprev = int(time.time()*10000)
            
            while not restart_event.is_set():  #and not shutdown_event.is_set():
                # inits
                did_vicon_request = False
                did_secodary_request = False
                retcode = 1
                is_on = request_pointer

                ### first Vitoconnect request -------------------
                if(serViCon is not None):
                    vidata = viconn_util.get_vicon_request()
                    if(vidata):
                        serViDev.reset_input_buffer()
                        serViDev.write(vidata)
                        c_logging.viconnlog.do_log(vidata, "M")
                        # recive response an pass bytes directly back to VitoConnect, 
                        # returns when response is complete (or error or timeout) 
                        retcode, _, redata = optolinkvs2.receive_vs2telegr(True, True, serViDev, serViCon, vicon_publ_callback)
                        c_logging.viconnlog.do_log(redata, f"S {retcode:02x}")
                        olbreath(retcode)
                        did_vicon_request = True

                ### secondary requests ------------------
                #TODO überlegen/testen, ob Vitoconnect request nicht auch in der Reihe reicht
                
                for i in range(num_tasks):
                    is_on = (request_pointer + i) % num_tasks
                    #print(f"{((tnow := int(time.time()*10000)) - tprev)} io {is_on}"); tprev = tnow

                    # polling list --------
                    if(is_on == 0):              
                        if(settings_ini.poll_interval >= 0):
                            if(poll_pointer < poll_list.num_items):
                                retcode = do_poll_item(poll_data, serViDev, mod_mqtt_util)
                                # increment poll pointer
                                poll_pointer += 1

                                #### everything to be done after poll cycle completed ++++++++++
                                if(poll_pointer >= poll_list.num_items):
                                    # remove once_onlies
                                    items_removed = False
                                    if(poll_cycle == 0):
                                        items_removed = poll_list.remove_once_onlies()
                                    # Viessdata csv
                                    if(items_removed):
                                        # no csv line if once_onlies were present
                                        # set up buffer according to remaining items
                                        poll_data = [None] * poll_list.num_items
                                    elif(settings_ini.write_viessdata_csv):
                                        viessdata_util.buffer_csv_line(poll_data)
                                    # wo1c energy
                                    if(settings_ini.wo1c_energy > 0) and (poll_cycle % settings_ini.wo1c_energy == 0):
                                        olbreath(retcode)
                                        retcode = wo1c_energy.read_energy(serViDev)
                                    # poll cycle control
                                    poll_cycle += 1
                                    if(poll_cycle == 479001600):  # 1*2*3*4*5*6*7*8*9*10*11*12 < 32 bits
                                        poll_cycle = 0
                                    # poll pointer control
                                    poll_pointer += 1  # wegen  on_polltimer(): if(poll_pointer > poll_list.num_items)
                                    if(settings_ini.poll_interval == 0):
                                        poll_pointer = 0  # else: poll_pointer gets reset by timer
                                    # #TEMP test
                                    # if(poll_cycle == 1):
                                    #     tcp_server.stop()
                                    # #TEMP test end
                                did_secodary_request = True

                    # MQTT request --------
                    elif(is_on == 1):
                        if(mod_mqtt_util is not None):
                            msg = mod_mqtt_util.get_mqtt_request()
                            if(msg):
                                try:
                                    retcode, _, _, resp = requests_util.response_to_request(msg, serViDev)
                                    mod_mqtt_util.publish_response(resp)
                                except Exception as e:
                                    mod_mqtt_util.publish_response(f"Error: {e}")
                                    logger.warning("Error handling MQTT request:", e)
                                did_secodary_request = True

                    # TCP/IP request --------
                    elif(is_on == 2):
                        if(tcp_server is not None):
                            msg = tcp_server.get_request()
                            if(msg):
                                #print(f"recd tcp msg: {msg}")
                                try:
                                    retcode, _, _, resp = requests_util.response_to_request(msg, serViDev)
                                    #print(f"try to send tcp: {resp}")
                                    tcp_server.send(resp)
                                except Exception as e:
                                    logger.warning("Error handling TCP request:", e)
                                did_secodary_request = True
        
                    #print(f"{((tnow := int(time.time()*10000)) - tprev)} ds {did_secodary_request}"); tprev = tnow
                            
                    if (did_secodary_request):
                        olbreath(retcode)
                        break

                # next time start with cheching next task first
                request_pointer = (is_on + 1) % num_tasks
                #print(f"{((tnow := int(time.time()*10000)) - tprev)} rp {request_pointer}"); tprev = tnow
                
                # let cpu take a breath if there was nothing to do
                if(not (did_vicon_request or did_secodary_request)):
                    time.sleep(0.005) 

    except Exception as e:
        excptn = e
        logger.error(excptn)
    finally:
        # sauber beenden: Tasks stoppen, VS1 Protokoll aktivieren(?), alle Verbindungen trennen
        progr_exit_flag = True
        # Schließen der seriellen Schnittstellen, Ausgabedatei, PollTimer, 
        logger.info("exit close...")
        logger.info("cancel poll timer") 
        timer_pollinterval.cancel()
        if(tcp_server is not None):
            tcp_server.stop()
        #tcp_thread.join()  #TODO ??
        viconn_util.exit_flag = True
        if(serViCon is not None):
            logger.info("closing serViCon")
            serViCon.close()
        if(serViDev is not None):
            if(serViDev.is_open and (not isinstance(excptn, OSError))):
                logger.info("reset Optolink protocol")
                serViDev.write(bytes([0x04]))
            logger.info("closing serViDev")
            serViDev.close()
        if(mod_mqtt_util is not None):
            mod_mqtt_util.exit_mqtt()
        if(c_logging.viconnlog.log_handle is not None):
            logger.info("closing vitolog")
            c_logging.viconnlog.close_log()

 
if __name__ == "__main__":
    main()
