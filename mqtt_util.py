import time
import json
import paho.mqtt.client as paho

import settings_ini

mqtt_client = None

def connect_mqtt() -> bool:
    global mqtt_client
    # Verbindung zu MQTT Broker herstellen (ggf) ++++++++++++++
    if(settings_ini.mqtt != None):
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, "OLswitch" + '_' + str(int(time.time()*1000)))  # Unique mqtt id using timestamp
        if(settings_ini.mqtt_user != None):
            mlst = settings_ini.mqtt_user.split(':')
            mqtt_client.username_pw_set(mlst[0], password=mlst[1])
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mlst = settings_ini.mqtt.split(':')
        mqtt_client.connect(mlst[0], int(mlst[1]))
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
        mqtt_client.loop_start()
        return True


# MQTT  +++++++++++++++++++++++++++++
cmnd_queue = []   # command queue to serialize bus traffic

def on_connect(client, userdata, flags, reason_code, properties):
    if settings_ini.mqtt_listen != None:
        client.subscribe(settings_ini.mqtt_listen)
    
def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print('mqtt broker disconnected. reason_code = ' + str(reason_code))

def on_message(client, userdata, msg):
    topic = str(msg.topic)            # Topic in String umwandeln
    if topic == settings_ini.mqtt_listen:
        try:
            payload = json.loads(msg.payload.decode())  # Payload in Dict umwandeln
            cmnd_queue.append(payload)
        except:
            print('bad payload: ' + str(msg.payload)+'; topic: ' + str(msg.topic))
            payload = ''

def listen(readdids=None, timestep=0):
    if(settings_ini.mqtt is None):
        raise Exception('mqtt option is mandatory for listener mode')

    def cmnd_loop():
        # cmnds = ['raw','read','write']   #,'read-all','write','write-raw']
        # if(readdids != None):
        #     jobs =  eval_complex_list(readdids)
        #     next_read_time = time.time()

        # while True:
        #     if len(cmnd_queue) > 0:
        #         cd = cmnd_queue.pop(0)

        #         if not cd['mode'] in cmnds:
        #             print('bad mode value = ' + str(cd['mode']) + '\nSupported commands are: ' + json.dumps(cmnds)[1:-1])

        #         elif cd['mode'] in ['read','read-json','read-raw']:
        #             addr = getaddr(cd)
        #             dids = cd['data']
        #             ensure_ecu(addr) 
        #             for did in dids:
        #                 readbydid(addr, getint(did), json=(cd['mode']=='read-json'), raw=(cd['mode']=='read-raw'))
        #                 time.sleep(0.01)            # 10 ms delay before next request

        #         elif cd['mode'] == 'read-pure':
        #             addr = getaddr(cd)
        #             dids = cd['data']
        #             ensure_ecu(addr) 
        #             for did in dids:
        #                 readpure(addr, getint(did))
        #                 time.sleep(0.01)            # 10 ms delay before next request

        #         elif cd['mode'] == 'read-all':
        #             addr = getaddr(cd)
        #             if(args.verbose == True):
        #                 print(f"reading {hex(addr)}, {dicEcus[addr].numdps} datapoints, please be patient...")
        #             lst = dicEcus[addr].readAll(args.raw)
        #             for itm in lst:
        #                 showread(addr=addr, did=itm[0], value=itm[1], idstr=itm[2])

        #         elif cd['mode'] == 'write':
        #             addr = getaddr(cd)
        #             ensure_ecu(addr)
        #             for wd in cd['data']:
        #                 didKey = getint(wd[0])    # key: convert numeric or string parameter to numeric value
        #                 if type(wd[1]) == str:
        #                     didVal = json.loads(wd[1])    # value: if string parse as json
        #                 else:
        #                     didVal = wd[1]  # value: if mqtt payload already parsed
        #                 dicEcus[addr].writeByDid(didKey, didVal, raw=False) 
        #                 time.sleep(0.1)
                    
        #         elif cd['mode'] == 'write-raw':
        #             addr = getaddr(cd)
        #             ensure_ecu(addr)
        #             for wd in cd['data']:
        #                 didKey = getint(wd[0])                  # key is submitted as numeric value
        #                 didVal = str(wd[1]).replace('0x','')    # val is submitted as hex string
        #                 dicEcus[addr].writeByDid(didKey, didVal, raw=True)
        #                 time.sleep(0.1)
        #     else:
        #         if (readdids != None):
        #             if (next_read_time > 0) and (time.time() > next_read_time):
        #                 # add dids to read to command queue
        #                 for ecudid in jobs:
        #                     cmnd_queue.append({'mode':'read', 'addr': ecudid[0], 'data': [ecudid[1]]})
        #                 if(timestep != None):
        #                     next_read_time = next_read_time + int(timestep)
        #                 else:
        #                     next_read_time = 0    # Don't do it again
                    
            time.sleep(0.01)

    print("Enter listener mode, waiting for commands on mqtt...")
    # and go...
    #cmnd_loop() 

def showread(name, addr, value):  
    if(mqtt_client != None):
        publishStr = settings_ini.mqtt_fstr.format(dpaddr = addr, dpname = name)
        # send
        ret = mqtt_client.publish(settings_ini.mqtt_topic + "/" + publishStr, value)    
        print(ret)
                

def exit_mqtt():
    if(mqtt_client != None):
        print("disconnect MQTT client")
        mqtt_client.disconnect()

    
# ------------------------
# main for test only
# ------------------------
def main():
    try:
        if connect_mqtt():
            print("connect ok")
            while(True):
                for i in range(10):
                    showread("TestVal", 0x0123, i)
                    time.sleep(0.7)
        else:
            print("fail")
    except Exception as e:
        print(e)
    finally:
        exit_mqtt()


if __name__ == "__main__":
    main()
