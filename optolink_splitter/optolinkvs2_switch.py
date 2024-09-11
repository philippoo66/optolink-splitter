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

version = "1.1.1.1"

import serial
import time
import threading
import importlib

import settings_ini
import optolinkvs2
import viconn_util
import viessdata_util
import tcpip_util
import requests_util
import utils

#global_exit_flag = False

def olbreath(retcode:int):
    if(retcode <= 0x03):
        # success, err msg
        time.sleep(0.1)
    elif(retcode in [0xFF, 0xAA]):
        # timeout, err_handle
        pass
    else:
        # allow calming down
        time.sleep(0.5)

# Vitoconnect logging
vitolog = None

def log_vito(data, pre):
    global vitolog
    if(vitolog is not None):
        sd = utils.bbbstr(data)
        vitolog.write(f"{pre}\t{int(time.time()*1000)}\t{sd}\n")


# polling list +++++++++++++++++++++++++++++
poll_pointer = 0

def do_poll_item(poll_data, ser:serial.Serial, mod_mqtt=None) -> int:  # retcode
    global poll_pointer
    val = "?"

    item = settings_ini.poll_items[poll_pointer]  # (Name, DpAddr, Len, Scale/Type, Signed)  
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
                while((poll_pointer + 1) < len(settings_ini.poll_items)):
                    next_idx = poll_pointer + 1
                    next_item = settings_ini.poll_items[next_idx]
                    # if next address same AND next len same AND next type starts with 'b:'
                    if((next_item[1] == item[1]) and (next_item[2] == item[2]) and (str(next_item[3]).lower()).startswith('b:')):
                        next_val = requests_util.perform_bytebit_filter(data, next_item)

                        # save val in buffer for csv
                        poll_data[next_idx] = next_val

                        if(mod_mqtt is not None): 
                            # post to MQTT broker
                            mod_mqtt.publish_read(next_item[0], next_item[1], next_val)

                        poll_pointer = next_idx
                    else:
                        break
    else:
        print(f"Error do_poll_item {poll_pointer}, Addr {item[1]:04X}, RetCode {retcode}, Data {val}")
    return retcode

# poll timer    
def on_polltimer():
    global poll_pointer
    if(poll_pointer > len(settings_ini.poll_items)):
        poll_pointer = 0
    startPollTimer(settings_ini.poll_interval)

timer_pollinterval = threading.Timer(1.0, on_polltimer)

def startPollTimer(secs:float):
    global timer_pollinterval
    timer_pollinterval.cancel()
    timer_pollinterval = threading.Timer(secs, on_polltimer)
    timer_pollinterval.start()




# ------------------------
# Main
# ------------------------
def main():
    global poll_pointer
    global vitolog

    try:
        mod_mqtt_util = None
        poll_data = [None] * len(settings_ini.poll_items)


        # serielle Verbidungen mit Vitoconnect und dem Optolink Kopf aufbauen ++++++++++++++
        serViCon = None  # Vitoconnect (Master)
        serViDev = None  # Viessmann Device (Slave)

        if(settings_ini.port_vitoconnect is not None):
            serViCon = serial.Serial(settings_ini.port_vitoconnect,
                        baudrate=4800,
                        parity=serial.PARITY_EVEN,
                        stopbits=serial.STOPBITS_TWO,
                        bytesize=serial.EIGHTBITS,
                        exclusive=True,
                        timeout=0)
        
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


        # Empfangstask der sekundären Master starten (TcpIp, MQTT)

        # MQTT --------
        if(settings_ini.mqtt is not None):
            # avoid paho.mqtt required if not used
            mod_mqtt_util = importlib.import_module("mqtt_util")
            mod_mqtt_util.connect_mqtt()


        # TCP/IP connection --------
        if(settings_ini.tcpip_port is not None):
            tcp_thread = threading.Thread(target=tcpip_util.tcpip4ever, args=(settings_ini.tcpip_port,False))
            tcp_thread.daemon = True  # Setze den Thread als Hintergrundthread - wichtig für Ctrl-C
            tcp_thread.start()


        # run VS2 connection ------------------
        if(serViCon is not None):
            # Vitoconncet logging
            if(settings_ini.log_vitoconnect):
                vitolog = open('vitolog.txt', 'a')
            # detect VS2 Protokol
            print("awaiting VS2...")
            vs2timeout = settings_ini.vs2timeout
            if not viconn_util.detect_vs2(serViCon, serViDev, vs2timeout, vitolog):
                raise Exception("VS2 protocol not detected within timeout", vs2timeout)
            print("VS detected")
            vicon_thread = threading.Thread(target=viconn_util.listen_to_Vitoconnect, args=(serViCon,vitolog))
            vicon_thread.daemon = True  # Setze den Thread als Hintergrundthread - wichtig für Ctrl-C
            vicon_thread.start()
        else:
            # VS2 Protokoll am Slave initialisieren
            if(not optolinkvs2.init_vs2(serViDev)):
                print("init_vs2 failed")
                raise Exception("init_vs2 failed")  # schlecht für KW Protokoll


        # Polling Mechanismus --------
        len_polllist = len(settings_ini.poll_items)
        if(settings_ini.poll_interval > 0) and (len_polllist > 0):
            startPollTimer(settings_ini.poll_interval)


        # Main Loop starten und Sachen abarbeiten
        request_pointer = 0
        while(True):
            tookbreath = False
            if(serViCon is not None):
                # first Vitoconnect request -------------------
                vidata = viconn_util.get_vicon_request()
                if(vidata):
                    serViDev.write(vidata)
                    log_vito(vidata, "M")
                    # recive response an pass bytes directly back to VitoConnect, 
                    # returns when response is complete (or error or timeout) 
                    retcode,_, redata = optolinkvs2.receive_vs2telegr(True, True, serViDev, serViCon)
                    log_vito(redata, "S")
                    olbreath(retcode)
                    tookbreath = True

            # secondary requests ------------------
            #TODO überlegen/testen, ob Vitoconnect request nicht auch in der Reihe reicht

            # polling list --------
            if(request_pointer == 0):              
                if(settings_ini.poll_interval < 0):
                    request_pointer += 1
                elif(poll_pointer < len_polllist):
                    retcode = do_poll_item(poll_data, serViDev, mod_mqtt_util)

                    poll_pointer += 1

                    if(poll_pointer == len_polllist):
                        if(settings_ini.write_viessdata_csv):
                            viessdata_util.buffer_csv_line(poll_data)
                        poll_pointer += 1
                        if(settings_ini.poll_interval == 0):
                            poll_pointer = 0
                    olbreath(retcode)
                    tookbreath = True
                else:
                    request_pointer += 1

            # MQTT request --------
            if(request_pointer == 1):
                if(mod_mqtt_util is None):
                    request_pointer += 1
                else:
                    msg = mod_mqtt_util.get_mqtt_request()
                    if(msg):
                        try:
                            retcode, _, _, resp = requests_util.response_to_request(msg, serViDev)
                            mod_mqtt_util.publish_response(resp)
                            olbreath(retcode)
                            tookbreath = True
                        except Exception as e:
                            print("Error handling MQTT request:", e)
                    else:
                        request_pointer += 1

            # TCP/IP request --------
            if(request_pointer == 2):
                if(settings_ini.tcpip_port is None):
                    request_pointer += 1
                else:
                    msg = tcpip_util.get_tcp_request()
                    if(msg):
                        try:
                            retcode, _, _, resp = requests_util.response_to_request(msg, serViDev)
                            tcpip_util.send_tcpip(resp)
                            olbreath(retcode)
                            tookbreath = True
                        except Exception as e:
                            print("Error handling TCP request:", e)
                    else:
                        request_pointer += 1

            # request_pointer control --------
            request_pointer += 1
            if(request_pointer > 2):
                request_pointer = 0
            
            # let cpu take a breath
            if(not tookbreath):
                time.sleep(0.005) 

    except KeyboardInterrupt:
        print("Abbruch durch Benutzer.")
    except Exception as e:
        print(e)
    finally:
        # sauber beenden: Tasks stoppen, VS1 Protokoll aktivieren(?), alle Verbindungen trennen
        # Schließen der seriellen Schnittstellen, Ausgabedatei, PollTimer, 
        print("exit close")
        if(serViCon is not None):
            print("closing serViCon")
            serViCon.close()
        if(serViDev is not None):
            if serViDev.is_open:
                print("reset protocol")
                serViDev.write([0x04])  #TODO yes or no?
                print("closing serViDev")
                serViDev.close()
        print("cancel poll timer ") 
        timer_pollinterval.cancel()
        tcpip_util.exit_tcpip()
        #tcp_thread.join()  #TODO ??
        if(mod_mqtt_util is not None):
            mod_mqtt_util.exit_mqtt()
        if(vitolog is not None):
            print("closing vitolog")
            vitolog.close()

 
if __name__ == "__main__":
    main()
