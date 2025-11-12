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

import time
import paho.mqtt.client as paho

import utils
import settings_ini
from logger_util import logger


verbose = False

mqtt_client = None
cmnd_queue = []   # command queue to serialize bus traffic
publ_queue = []   # stuff to get published

recent_posts = {}
reset_recent = False
_sentinel = object()  # eindeutiger Wert für "nicht vorhanden"


def on_connect(client, userdata, flags, reason_code, properties):
    if settings_ini.mqtt_listen != None:
        client.subscribe(settings_ini.mqtt_listen)
    mqtt_client.publish(settings_ini.mqtt_topic + "/LWT" , "online", qos=0,  retain=True)
    
def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print('mqtt broker disconnected. reason_code = ' + str(reason_code))
    mqtt_client.publish(settings_ini.mqtt_topic + "/LWT" , "offline", qos=0,  retain=True)

def on_message(client, userdata, msg):
    global reset_recent
    #print("MQTT recd:", msg.topic, msg.payload)
    if(settings_ini.mqtt_listen is None):
        print(f"MQTT recd: Topic = {msg.topic}, Payload = {msg.payload}")  # ErrMsg oder so?
        return
    topic = str(msg.topic)            # Topic in String umwandeln
    if topic == settings_ini.mqtt_listen:
        rec = utils.bstr2str(msg.payload)
        rec = rec.replace(' ','').replace('\0','').replace('\n','').replace('\r','').replace('"','').replace("'","")
        if(rec.lower() in ('reset', 'resetrecent')):
            reset_recent = True
        else:
            cmnd_queue.append(rec) 
    else:
        # Ausgabe anderer eingehenden MQTT-Nachrichten
        print(f"MQTT recd: Topic = {msg.topic}, Payload = {msg.payload}")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_log(client, userdata, level, buf):
    print("MQTT Log:", buf)


def connect_mqtt():
    global mqtt_client
    try:
        # Verbindung zu MQTT Broker herstellen ++++++++++++++
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, "olswitch") # + '_' + str(int(time.time()*1000)))  # Unique mqtt id using timestamp
        if(settings_ini.mqtt_user is not None):
            mlst = settings_ini.mqtt_user.split(':')
            mqtt_client.username_pw_set(mlst[0], password=mlst[1])
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.will_set(settings_ini.mqtt_topic + "/LWT", "offline", qos=0,  retain=True)
        if(settings_ini.mqtt_listen != None):
            mqtt_client.on_subscribe = on_subscribe
        if(settings_ini.mqtt_logging):
            mqtt_client.on_log = on_log
            mqtt_client.enable_logger()  # Muss VOR dem connect() aufgerufen werden
            mqtt_client._logger.setLevel("DEBUG")  # Optional – Level auf DEBUG setzen
        mlst = settings_ini.mqtt.split(':')
        mqtt_client.connect(mlst[0], int(mlst[1]))
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
        mqtt_client.loop_start()
        # preparations
        if(settings_ini.mqtt_fstr is None):
            settings_ini.mqtt_fstr = "{dpname}"
    except Exception as e:
        raise Exception("Error connecting MQTT: " + str(e))

def get_mqtt_request() -> str:
    ret = ""
    if len(cmnd_queue) > 0:
        ret = cmnd_queue.pop(0)
    return ret

def publish_read(name, addr, value):
    if(mqtt_client != None):
        publishStr = settings_ini.mqtt_fstr.format(dpaddr = addr, dpname = name)
        # send
        ret = publish_smart(settings_ini.mqtt_topic + "/" + publishStr, value, retain=settings_ini.mqtt_retain)    
        if(verbose): print(ret)

def publish_response(resp:str):
    if(mqtt_client != None):
        # always publish responses
        ret = mqtt_client.publish(settings_ini.mqtt_respond, resp)    
        if(verbose): print(ret)


def publish_smart(topic, value, qos=0, retain=False):
    global reset_recent
    if(mqtt_client != None):
        if(settings_ini.mqtt_no_redundant):
            if(reset_recent):
                recent_posts.clear()
                reset_recent = False
                publish_response("previous values cleared")
            # Publish only if the value changed
            last = recent_posts.get(topic, _sentinel)
            if last == value:
                return
            recent_posts[topic] = value
        ret = mqtt_client.publish(topic, value, qos=qos, retain=retain)
        if(verbose): print(ret)


def exit_mqtt():
    if(mqtt_client != None):
        logger.info("disconnect MQTT client")
        if(mqtt_client.is_connected):
            mqtt_client.publish(settings_ini.mqtt_topic + "/LWT" , "offline", qos=0,  retain=True)
        mqtt_client.disconnect()

    
# ------------------------
# main for test only
# ------------------------
def main():
    try:
        connect_mqtt()
        print("connect ok")
        while(True):
            for i in range(10):
                publish_read("TestVal", 0x0123, i)
                time.sleep(3)
        # else:
        #     print("fail")
    except Exception as e:
        print(e)
    finally:
        exit_mqtt()


if __name__ == "__main__":
    main()
