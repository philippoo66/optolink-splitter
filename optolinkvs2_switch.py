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

VERSION = "1.11.0.2"

import serial
import time
import threading
import importlib
import json
import signal

from c_settings_adapter import settings  # to be done first to get logger settings
from logger_util import logger
import vs12_adapter
import viconn_util
import viessdata_util
import c_tcpserver
import requests_util
from c_logging import viconnlog
from c_polllist import poll_list
import utils
import wo1c_energy
import c_LoggingSerial

# exit flag e.g. to stop endless loops
progr_exit_flag = False

# ether objects
mod_mqtt = None
tcp_server = None


last_vs1_comm = 0

force_poll_flag = False
reload_poll_flag = False

num_vicon_tries = 0
num_restarts = 0


# === polling =============================
poll_pointer = 0
poll_cycle = 0

def do_poll_item(poll_data, ser:serial.Serial, item_index:int=None) -> int:  # retcode      # type: ignore
    # set item_index to force poll
    global poll_pointer
    val = "?"
    item = "?"

#    print("do_poll_item",item_index)
    try:
        # handle PollCycle option +++++++++++++++++++++++
        # loop though poll items until find one to be done this cycle
        while(True):
            list_index = item_index if item_index else poll_pointer
            item = poll_list.items[list_index]  # (PollCycleGroupKey, Name, DpAddr, Len, Scale/Type, Signed)
            item_cycle = poll_list.cycle_groups[item[0]]

            if(item_index is None) and ((item_cycle < 0) or ((item_cycle > 0) and (poll_cycle % item_cycle != 0)) or ((item_cycle == 0) and (poll_cycle != 0))):
                # ---------------------------------------
                # +++ do NOT poll this item this time +++
                # ---------------------------------------

                # leave poll_data[poll_pointer] unchanged

                poll_pointer += 1
                if(poll_pointer == poll_list.num_items):
                    # no further item this cycle
                    return 0xAB

            else:
                # remove PollCycleGroupKey for further processing
                item = item[1:]
                break

        retcode, data, val, _ = requests_util.response_to_request(item, ser)

        if(retcode == 0x01):
            # save val in buffer for csv
            poll_data[list_index] = val

            # post to MQTT broker
            if(mod_mqtt is not None): 
                mod_mqtt.publish_read(item[0], item[1], val)

            # probably more bytebit values of the same datapoint?!
            if(len(item) > 3):
                if(str(item[3]).lower().startswith('b:')):
                    # bytebit filter +++++++++
                    while((list_index + 1) < poll_list.num_items):
                        list_index += 1
                        next_item = poll_list.items[list_index]
                        # remove PollCycle in case
                        next_item = next_item[1:]
                        
                        # if next address same AND next len same AND next type starts with 'b:'
                        if((len(next_item) > 3) and (next_item[1] == item[1]) and (next_item[2] == item[2]) and (str(next_item[3]).lower()).startswith('b:')):
                            next_val = requests_util.perform_bytebit_filter_and_evaluate(data, next_item)

                            # save val in buffer for csv
                            poll_data[list_index] = next_val

                            if(mod_mqtt is not None): 
                                # publish to MQTT broker
                                mod_mqtt.publish_read(next_item[0], next_item[1], next_val)

                            poll_pointer = list_index
                        else:
                            break
        else:
            logger.error(f"OL Error do_poll_item {poll_pointer}, Addr {item[1]:04X}, RetCode {retcode}, Data {val}")
        return retcode
    except Exception as e:
        logger.error(f"Error do_poll_item {poll_pointer}, {item}: {e}")
        raise


# poll timer +++++++++++++++
def on_polltimer():
    global poll_pointer
    if(poll_pointer > poll_list.num_items):
        poll_pointer = 0
    startPollTimer(settings.poll_interval)

timer_pollinterval = threading.Timer(1.0, on_polltimer)

def startPollTimer(secs:float):
    global timer_pollinterval
    timer_pollinterval.cancel()
    timer_pollinterval = threading.Timer(secs, on_polltimer)
    timer_pollinterval.start()


def olbreath(retcode:int):
    """
    give vitotronic some time between comms to do other things
    """
    global last_vs1_comm
    if(retcode <= 0x03):
        # success, err msg
        if(settings.vs1protocol):
            last_vs1_comm = time.monotonic()
            vs12_adapter.reset_vs1sync()
        time.sleep(settings.olbreath)
    elif(retcode in [0xFF, 0xAA, 0xAB]):
        # timeout, err_handle, final item skipped in cycle
        pass
    else:
        if(settings.vs1protocol):
            last_vs1_comm = time.monotonic()
            vs12_adapter.reset_vs1sync()
        # allow calming down
        time.sleep(2 * settings.olbreath)


# Vicon listener +++++++++++++++++++++++++++++
def vicon_thread_func(serViCon, serViDev):
    """
    Thread to receive Vitoconnect requests
    """
    print("running Vitoconnect listener")
    try:
        callback = mqtt_publ_viconn if settings.viconn_to_mqtt else None
        viconn_util.exit_flag = False
        viconn_util.listen_to_Vitoconnect(serViCon, callback)
    except Exception as e:
        msg = f"Error in listen_to_Vitoconnect: {e}"
        viconnlog.do_log(msg)
        logger.error(f"{msg} -> re-init")
        mqtt_publ_debug(msg)
        viconn_util.exit_flag = True
        utils.restart_event.set()  # Hauptprogramm signalisiert, dass ein Neustart noetig ist
        return  # Thread wird beendet


# TCP loop +++++++++++++++++++++++++++++
def tcp_connection_loop():
    global tcp_server
    while(not progr_exit_flag):
        tcp_server = c_tcpserver.TcpServer("0.0.0.0", settings.tcpip_port) #, verbose=True)
        tcp_server.command_callback = do_special_command        # type: ignore
        tcp_server.run()
        tcp_server = None
        if progr_exit_flag: return
        #logger.info("TCP session closed, restart soon...")
        time.sleep(1)


# utils +++++++++++++++++++++++++++++
def do_special_command(cmnd:str, source:int=1) -> bool:  # source: 1:MQTT, 2:TCP, 0:no response
    global force_poll_flag, reload_poll_flag

    try:
        resp =  f"{cmnd} failed"
        cmnd = cmnd.replace(" ", "")
        if not cmnd: 
            return False
        parts = cmnd.split(";")
        #print("do_special_command",cmnd)
        if parts[0] in ('reset', 'resetrecent'):
            if(mod_mqtt is not None):
                mod_mqtt.reset_recent = True        # type: ignore
                resp = f"{parts[0]} triggered"
        elif parts[0] in ('forcepoll',):
            force_poll_flag = True
            resp = f"{parts[0]} triggered"
        elif parts[0] in ('reloadpoll',):   
            reload_poll_flag = True
            resp = f"{parts[0]} triggered"
        elif parts[0] in ("exit", "resettcp"):
            if tcp_server:
                tcp_server.stop()
                resp = f"{parts[0]} triggered" if source != 2 else ''
        elif parts[0] in ("flushcsv",):
            if settings.write_viessdata_csv:
                viessdata_util.buffer_csv_line([], True)
                resp = f"{parts[0]} triggered"
        elif parts[0] in ("reini", "reloadini"):
            # some changes (like ser ports) will not take effect...
            settings.set_settings(reload=True)
            resp = f"ini settings reloaded"
        elif parts[0] in ("setpollcycle", "setcycle"):
            if poll_list.set_pollcycle(parts[1], parts[2]):
                resp = f"cycle_group {parts[1]} set to {parts[2]}"
        elif parts[0] in ("setpollinterval", "setinterval"):
            settings.poll_interval = int(parts[1])
            resp = f"poll_interval set to {parts[1]}"
        else:
            return False
    except Exception as e:
        resp = str(e)
    # responde
    if(resp):
        if(source == 1):
            if(mod_mqtt):
                mod_mqtt.publish_response(resp)
        elif(source == 2):
            if(tcp_server):
                tcp_server.send(resp)
    return True


def publish_stat():
    if(mod_mqtt is not None) and mod_mqtt.mqtt_client.is_connected:
        topic = settings.mqtt_topic + "/stats"
        jdata = {"Splitter Version" : VERSION,
                "Splitter started" : str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))),
                "Poll List Make" : str(poll_list.module_date)}
        mod_mqtt.publish_smart(topic, json.dumps(jdata))


def reset_retry_counters_in(delay_minutes=30):
    global num_restarts, num_vicon_tries
    
    def reset():
        global num_restarts, num_vicon_tries
        num_restarts = 0
        num_vicon_tries = 0

    timer = threading.Timer(delay_minutes * 60, reset)
    timer.start()


def mqtt_publ_debug(msg:str):
    if(mod_mqtt is not None) and mod_mqtt.mqtt_client.is_connected:
        mod_mqtt.mqtt_client.publish(settings.mqtt_topic + "/debug", msg)  


# MQTT publish callback VS2 +++++++++++++++++++++++++++++
def mqtt_publ_viconn(retcd, addr, data, msgid, msqn, fctcd, dlen):
    if(mod_mqtt is not None) and mod_mqtt.mqtt_client.is_connected:
        if addr:
            topic = settings.mqtt_topic + f"/viconn/{addr:04X}/{get_msgid(msgid)}"
            jdata = {"retcode" : get_retcode(retcd),
                    "fctcode" : get_fctcode(fctcd),
                    "datalen" : dlen,
                    "data" : f"0x{utils.arr2hexstr(data)}" if data else "none"}
            mod_mqtt.publish_smart(topic, json.dumps(jdata))

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

# MQTT publish callback VS1 +++++++++++++++++++++++++++++

# digs = len(str(settings.viconnVS1_ringbuff))
# rb_pointer = 0
def mqtt_publ_viconnVS1(data, request:bool):
    global rb_pointer 
    if(mod_mqtt is not None) and mod_mqtt.mqtt_client.is_connected:
        if(request):
            pass
            
        topic = settings.mqtt_topic + f"/viconn/{'Vicon' if request else 'Opto'}"
        mod_mqtt.publish_smart(topic, utils.bbbstr(data))

def get_fctcodeVS1(val):
    strg = dicFunctionCodesVS1.get(val) 
    if strg: return strg
    else: return f"0x{val:02X}"

dicFunctionCodesVS1 = {
    0xF4 : "Virtuell_Write", 
    0xF7 : "Virtuell_Read",
    0x68 : "GFA_Write", 
    0x6B : "GFA_Read", 
    0x78 : "PROZESS_WRITE", 
    0x7B : "PROZESS_READ" 
}


# signal handling
def handle_exit(sig, frame):
    logger.info(f"received signal {sig}")
    utils.shutdown_event.set()
    raise(SystemExit)


# ------------------------
# Main
# ------------------------
def main():
    global mod_mqtt
    global poll_pointer, poll_cycle
    global force_poll_flag, reload_poll_flag
    global num_restarts, num_vicon_tries, progr_exit_flag

    # Signale abfangen fuer sauberes Beenden
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)


    # some variables ++++++
    serOptolink = None  # Viessmann Device (Slave)
    serVitoConnnect = None  # Vitoconnect (Master)

    excptn = None
    first_time = True


    # === the method for a clean exit =============================
    def close_everything():
        """
        sauber beenden: Tasks stoppen, VS1 Protokoll aktivieren(?), alle Verbindungen trennen        
        """
        global progr_exit_flag
        nonlocal serOptolink, serVitoConnnect, excptn
        
        progr_exit_flag = True
        # Schliessen der seriellen Schnittstellen, Ausgabedatei, PollTimer, 
        logger.info("exit close...")
        logger.info("cancel poll timer") 
        timer_pollinterval.cancel()
        if(tcp_server is not None):
            tcp_server.stop()
        viconn_util.exit_flag = True
        if(serVitoConnnect is not None):
            logger.info("closing serVitoConnnect")
            serVitoConnnect.close()
            serVitoConnnect = None  #?
        if(serOptolink is not None):
            if(serOptolink.is_open and (not isinstance(excptn, OSError))):
                logger.info("reset Optolink protocol")
                serOptolink.write(bytes([0x04]))
            logger.info("closing serOptolink")
            serOptolink.close()
        if(mod_mqtt is not None):
            mod_mqtt.exit_mqtt()
        if(viconnlog.log_handle is not None):
            logger.info("closing viconnlog")
            viconnlog.close_log()


    logger.info(f"Version {VERSION}")

    # ++++++++++++++++++++
    # the re-start loop
    # ++++++++++++++++++++      
    while not utils.shutdown_event.is_set():
        try:
        #if True:

            if first_time:
                # do not restart in case of poll list problem
                utils.shutdown_event.set()
                # ---------------------
                # init the poll list 
                # ---------------------
                poll_list.make_list()
                # buffer for read data for writing viessdata.csv 
                poll_data = [None] * poll_list.num_items

                utils.shutdown_event.clear()
                first_time = False
            else:
                # === this is a re-start ======
                num_restarts += 1
                if num_vicon_tries > settings.max_vicon_tries:
                    # continue without vitoconnect 
                    settings.port_vitoconnect = None
                progr_exit_flag = False
                utils.restart_event.clear()
                excptn = None
                reset_retry_counters_in(settings.retry_counters_reset)
                logger.info(f"re-start #{num_restarts}")

            # ---------------------
            # open serial ports 
            # ---------------------

            # serielle Verbindungen mit dem Optolink Kopf oeffnen ++++++++++++++
            if(settings.port_optolink is not None):
                serial_args = dict(
                    port=settings.port_optolink,
                    baudrate=4800,
                    parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_TWO,
                    bytesize=serial.EIGHTBITS,
                    exclusive=True,
                    timeout=0,
                )

                if settings.log_optolink:
                    logger.info("Optolink using LoggingSerial")
                    serOptolink = c_LoggingSerial.LoggingSerial(**serial_args,
                            # specials
                            logger_name="optolink",
                            logger_fmt="%(relativeCreated)d: %(message)s",
                            logger_no_console = True,
                            logger_max_bytes = 25 * 1024 * 1024  # 25 MB
                        )
                else:
                    serOptolink = serial.Serial(**serial_args)      # type: ignore

                # open went fine
                logger.info("Optolink serial port opened")
            else:
                utils.shutdown_event.set()
                raise Exception("ERROR: Optolink device is mandatory!")

            # serielle Verbindungen mit dem Vitoconnect oeffnen ++++++++++++++
            if(settings.port_vitoconnect is not None):
                serVitoConnnect = serial.Serial(settings.port_vitoconnect,
                            baudrate=4800,
                            parity=serial.PARITY_EVEN,
                            stopbits=serial.STOPBITS_TWO,
                            bytesize=serial.EIGHTBITS,
                            exclusive=True,
                            timeout=0)
                # open went fine
                logger.info("Vitoconnect serial port opened")

            # -------------------------------------------------------------
            # run the receive tasks of 'secondary masters' (MQTT, TcpIp) 
            # -------------------------------------------------------------

            # MQTT --------
            if(settings.mqtt_broker is not None):
                # avoid paho.mqtt required if not used
                mod_mqtt = importlib.import_module("mqtt_util")
                mod_mqtt.connect_mqtt()
                mod_mqtt.command_callback = do_special_command      # type: ignore


            # TCP/IP connection --------
            if(settings.tcpip_port is not None):
                tcp_thread = threading.Thread(target=tcp_connection_loop, daemon=True)
                tcp_thread.start()

            # ---------------------
            # some inits 
            # ---------------------

            # one wire value check init
            requests_util.init_w1_values_check()

            # publish viconn or not
            vicon_publ_callback = mqtt_publ_viconn if settings.viconn_to_mqtt else None

            # show what we have
            publish_stat()

            # ----------------------
            # run VS2 connection 
            # ----------------------

            if(serVitoConnnect is not None):
                num_vicon_tries += 1

                # reset vicon_request buffer
                viconn_util.vicon_request = bytearray()

                # Vitoconncet logging
                if(settings.log_vitoconnect):
                    if(viconnlog.log_handle is None):
                        viconnlog.open_log()

                # detect/init Protokol ++++++++++++
                logger.info("awaiting Vitoconnect being operational...")
                if not vs12_adapter.wait_for_vicon(serVitoConnnect, serOptolink, settings.vs2timeout):      # type: ignore
                    raise Exception("Vitoconnect not detected operational within timeout")
                msg = "Vitoconnect detected operational"
                viconnlog.do_log(msg)           
                logger.info(msg)

                # listen to vicon ++++++++++++
                # run reception thread
                
                vicon_thread = threading.Thread(target=vicon_thread_func, args=(serVitoConnnect, serOptolink), daemon=True)
                vicon_thread.start()

            else:
                # Protokoll/Kommunikation am Slave initialisieren
                spr = "VS2/300" if not settings.vs1protocol else "VS1/KW"
                if(not vs12_adapter.init_protocol(serOptolink)):        # type: ignore
                    raise Exception(f"init_protocol {spr} failed")  # schlecht fuer KW Protokoll
                logger.info(f"{spr} protocol initialized")


            # Polling Mechanismus --------
            if(settings.poll_interval > 0) and (poll_list.num_items > 0):
                startPollTimer(settings.poll_interval)

            # main loop initialisieren --------
            num_tasks = 3
            request_pointer = 0
            #tprev = int(time.time()*10000)
            logger.info("enter main loop")

            # +++++++++++++++++++++++++++            
            # main loop - Sachen abarbeiten 
            # +++++++++++++++++++++++++++            
            while not utils.restart_event.is_set():  #and not shutdown_event.is_set():
                # inits
                did_vicon_request = False
                did_secodary_request = False
                retcode = 1
                is_on = request_pointer

                ### first Vitoconnect request -------------------
                if(serVitoConnnect is not None):
                    vidata = viconn_util.get_vicon_request()
                    if(vidata):
                        serOptolink.reset_input_buffer()
                        serOptolink.write(vidata)
                        viconnlog.do_log(vidata, "M")
                        # recive response an pass bytes directly back to VitoConnect, 
                        # returns when response is complete (or error or timeout) 
                        retcode, _, redata = vs12_adapter.receive_telegr(True, True, serOptolink, serVitoConnnect, vicon_publ_callback)     # type: ignore
                        viconnlog.do_log(redata, f"S {retcode:02x}")
                        olbreath(retcode)
                        did_vicon_request = True

                ### secondary requests ------------------
                #TODO ueberlegen/testen, ob Vitoconnect request nicht auch in der Reihe reicht
                
                for i in range(num_tasks):
                    is_on = (request_pointer + i) % num_tasks
                    #print(f"{((tnow := int(time.time()*10000)) - tprev)} io {is_on}"); tprev = tnow

                    # polling list --------
                    if(is_on == 0):
                        if(poll_list.items):
                            # === action commands =================
                            # force poll including onceonlies
                            if force_poll_flag:
                                poll_pointer = 0
                                poll_cycle = 0
                                force_poll_flag = False
                                if(mod_mqtt): 
                                    mod_mqtt.lst_force_refresh = []     # type: ignore
                            # reload poll list, including onceonlies
                            if reload_poll_flag:
                                poll_list.make_list(reload=True)
                                if(len(poll_data) != poll_list.num_items):          # type: ignore
                                    poll_data = [None] * poll_list.num_items
                                publish_stat()
                                poll_pointer = 0
                                poll_cycle = 0
                                reload_poll_flag = False
                                if(mod_mqtt): 
                                    mod_mqtt.lst_force_refresh = []     # type: ignore

                            # === check if something is forced =================
                            if mod_mqtt and ((force_refresh_index := mod_mqtt.is_forced()) is not None):
                                retcode = do_poll_item(poll_data, serOptolink, item_index=force_refresh_index)      # type: ignore
                                # we did something
                                did_secodary_request = True

                            # === else do common poll if is on =================
                            elif(0 <= poll_pointer < poll_list.num_items):
                                retcode = do_poll_item(poll_data, serOptolink)      # type: ignore
                                # increment poll pointer
                                poll_pointer += 1

                                # +++ everything to be done after poll cycle completed ++++++++++
                                if(poll_pointer >= poll_list.num_items):
                                    # Viessdata csv
                                    if(settings.write_viessdata_csv):
                                        viessdata_util.buffer_csv_line(poll_data)       # type: ignore
                                    
                                    # wo1c energy
                                    if(settings.wo1c_energy > 0) and (poll_cycle % settings.wo1c_energy == 0):
                                        if(not settings.vs1protocol):
                                            olbreath(retcode)
                                            retcode = wo1c_energy.read_energy(serOptolink)      # type: ignore
                                        else:
                                            logger.warning("wo1c_energy not supported with VS1/KW protocol")
                                            settings.wo1c_energy = 0
                                    
                                    # poll cycle control
                                    poll_cycle += 1
                                    if(poll_cycle == 479001600):  # 1*2*3*4*5*6*7*8*9*10*11*12 < 32 bits
                                        poll_cycle = 0

                                    # poll pointer control
                                    poll_pointer += 1  # wegen  on_polltimer(): if(poll_pointer > poll_list.num_items)
                                    if(settings.poll_interval == 0):
                                        # continuous polling
                                        poll_pointer = 0  # else: poll_pointer gets reset by timer
                                
                                # we did something
                                did_secodary_request = True

                    # MQTT request --------
                    elif(is_on == 1):
                        if(mod_mqtt is not None):
                            msg = mod_mqtt.get_mqtt_request()
                            if(msg):
                                try:
                                    retcode, _, _, resp = requests_util.response_to_request(msg, serOptolink)
                                    mod_mqtt.publish_response(resp)
                                except Exception as e:
                                    mod_mqtt.publish_response(f"Error: {e}")
                                    logger.warning(f"Error handling MQTT request: {e}")
                                did_secodary_request = True

                    # TCP/IP request --------
                    elif(is_on == 2):
                        if(tcp_server is not None):
                            msg = tcp_server.get_request()
                            if(msg):
                                #print(f"recd tcp msg: {msg}")  #temp
                                try:
                                    retcode, _, _, resp = requests_util.response_to_request(msg, serOptolink)
                                    #print(f"retcode {retcode}, try to send tcp: {resp}")  #temp
                                    tcp_server.send(resp)
                                except Exception as e:
                                    logger.warning(f"Error handling TCP request: {e}")
                                did_secodary_request = True
        
                    #print(f"{((tnow := int(time.time()*10000)) - tprev)} ds {did_secodary_request}"); tprev = tnow
                            
                    if (did_secodary_request):
                        olbreath(retcode)
                        break

                # next time start with cheching next task first
                request_pointer = (is_on + 1) % num_tasks
                #print(f"{((tnow := int(time.time()*10000)) - tprev)} rp {request_pointer}"); tprev = tnow

                # keep-alive with vs1 
                if(settings.vs1protocol):
                    if(time.monotonic() > last_vs1_comm + 0.5):
                        retcode,_,_ = vs12_adapter.read_datapoint_ext(0xf8, 2, serOptolink)     # type: ignore
                        olbreath(retcode)
                        did_secodary_request = True

                # let cpu take a breath if there was nothing to do
                if not (did_vicon_request or did_secodary_request):
                    time.sleep(0.005) 
                
        except Exception as e:
            excptn = e
            logger.error(excptn)
        finally:
            close_everything()
            if utils.shutdown_event.is_set():
                return
            elif num_restarts >= settings.max_restarts:
                logger.error("too many restarts - exit script")
                return
            else:
                time.sleep(settings.restart_delay)


if __name__ == "__main__":
    main()
