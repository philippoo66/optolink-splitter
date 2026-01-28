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
import threading
import paho.mqtt.client as paho

from c_settings_adapter import settings
from logger_util import logger
from c_polllist import poll_list
import utils



verbose = False

mqtt_client = None
cmnd_queue = []   # command queue to serialize bus traffic
publ_queue = []   # stuff to get published

recent_posts = {}
reset_recent = False
_sentinel = object()  # eindeutiger Wert fuer "nicht vorhanden"

# callback for 'special' commands
command_callback = None


def on_connect(client, userdata, flags, reason_code, properties):
    # publish LWT online
    client.publish(settings.mqtt_topic + "/LWT" , "online", qos=0,  retain=True)
    # Subscribe to /set topics for writable datapoints
    subscriptions = [
        (settings.mqtt_topic + "/+/set", 0),
        (settings.mqtt_topic + "/+/+/set", 0),
        (settings.mqtt_topic + "/+/+/+/set", 0),
    ]
    if settings.mqtt_listen != None:
        subscriptions.append((settings.mqtt_listen, 0))
    client.subscribe(subscriptions)
    logger.debug(f"Subscribed to topic patterns: {subscriptions}")
    
def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        logger.warning('mqtt broker disconnected. reason_code = ' + str(reason_code))
    client.publish(settings.mqtt_topic + "/LWT" , "offline", qos=0,  retain=True)

def on_message(client, userdata, msg):
    logger.debug(f"MQTT recd: {msg.topic}, {msg.payload}")
    if(settings.mqtt_listen is None):
        logger.warning(f"MQTT recd: Topic = {msg.topic}, Payload = {msg.payload}")  # ErrMsg oder so?
        return
    topic = str(msg.topic)            # Topic in String umwandeln
    
    # Check if this is a /set topic
    if topic.endswith('/set') and settings.mqtt_topic and topic.startswith(settings.mqtt_topic + '/'):
        handle_set_topic(topic, msg.payload)
    elif topic == settings.mqtt_listen:
        rec = utils.bstr2str(msg.payload)
        rec = rec.replace(' ','').replace('\0','').replace('\n','').replace('\r','').replace('"','').replace("'","")
        if(command_callback) and command_callback(rec):
            pass
        else:
            cmnd_queue.append(rec) 
    else:
        # Ausgabe anderer eingehenden MQTT-Nachrichten
        logger.warning(f"MQTT recd: Topic = {msg.topic}, Payload = {msg.payload}")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        logger.error(f"MQTT Broker rejected you subscription: {reason_code_list[0]}")
    else:
        logger.info(f"MQTT Broker granted the following QoS: {reason_code_list[0].value}")

def on_log(client, userdata, level, buf):
    logger.info(f"MQTT [{level}]:", buf)


def connect_mqtt(): 
    global mqtt_client
    #try:  # exception handled in calling proc
    # Verbindung zu MQTT Broker herstellen ++++++++++++++
    clientid = "olswitch_" + settings.mqtt_topic.replace("/", "").replace(" ", "")
    try:
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, clientid) # + '_' + str(int(time.time()*1000)))  # Unique mqtt id using timestamp
    except:
        mqtt_client = paho.Client(client_id=clientid) # + '_' + str(int(time.time()*1000)))  # Unique mqtt id using timestamp

    # MQTT Username/Password (mqtt_user = "<user>:<pwd>" or None for anonymous)
    creds = settings.mqtt_user
    if creds is not None:
        creds = str(creds).strip()
        if creds != "":
            if ":" in creds:
                user, pwd = creds.split(":", 1)  # split once; allows ":" inside password
                mqtt_client.username_pw_set(user, password=(pwd if pwd != "" else None))
            else:
                mqtt_client.username_pw_set(creds, password=None)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    mqtt_client.will_set(settings.mqtt_topic + "/LWT", "offline", qos=0, retain=True)
    if(settings.mqtt_listen != None):
        mqtt_client.on_subscribe = on_subscribe
    if(settings.mqtt_logging):
        mqtt_client.on_log = on_log
        mqtt_client.enable_logger()  # Muss VOR dem connect() aufgerufen werden
        mqtt_client._logger.setLevel("DEBUG")  # Optional – Level auf DEBUG setzen  # type: ignore
    # Optional TLS / SSL
    if settings.mqtt_tls_enable:
        import ssl
        skip = bool(settings.mqtt_tls_skip_verify)
        ca_path = settings.mqtt_tls_ca_certs
        certfile = settings.mqtt_tls_certfile
        keyfile  = settings.mqtt_tls_keyfile
        if (certfile is not None and keyfile is None) or (keyfile is not None and certfile is None):
            raise Exception("For mTLS you must set mqtt_tls_certfile AND mqtt_tls_keyfile")
        mqtt_client.tls_set(
            ca_certs=ca_path,  # None => OS CA store
            certfile=certfile,
            keyfile=keyfile,
            cert_reqs=(ssl.CERT_NONE if skip else ssl.CERT_REQUIRED),
            tls_version=getattr(ssl, "PROTOCOL_TLS_CLIENT", ssl.PROTOCOL_TLS),
        )
        # IP / hostname mismatch and for "skip verify" mode
        mqtt_client.tls_insecure_set(skip)
    mlst = settings.mqtt_broker.split(':')      # type: ignore
    mqtt_client.connect(mlst[0], int(mlst[1]))
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
    mqtt_client.loop_start()
    # preparations
    if(settings.mqtt_fstr is None):
        settings.mqtt_fstr = "{dpname}"
    #except Exception as e:
    #    raise Exception("Error connecting MQTT: " + str(e))


def get_mqtt_request() -> str:
    if cmnd_queue:
        return cmnd_queue.pop(0)
    return ""


def publish_read(name, addr, value):
    if mqtt_client is not None:
        # Round float values to 1 decimal to stabilize sensor jitter (esp. w1 sensors)
        if isinstance(value, float):
            value = round(value, 1)
        publishStr = settings.mqtt_fstr.format(dpaddr=addr, dpname=name)
        # send
        ret = publish_smart(settings.mqtt_topic + "/" + publishStr, value, retain=settings.mqtt_retain)
        if verbose:
            print(ret)


def publish_response(resp:str):
    if(mqtt_client != None):
        # always publish responses
        ret = mqtt_client.publish(settings.mqtt_respond, resp)    
        if(verbose): print(ret)


def publish_smart(topic, value, qos=0, retain=False):
    global reset_recent
    if(mqtt_client != None):
        if(settings.mqtt_no_redundant):
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
        if(mqtt_client.is_connected()):
            mqtt_client.publish(settings.mqtt_topic + "/LWT" , "offline", qos=0,  retain=True)
        mqtt_client.disconnect()


######################################################
# ++  /set funtionality  +++++++++++++++++++++++++++++
# ++  Copyright 2026 manuboek, modified by philippoo66


#TODO
# - bbFilter sachen abfangen
# - strings schreibbar


# list of indexes of poll_list items to get refreshed immediately after got written
lst_force_refresh = []


def is_forced():
    if lst_force_refresh:
        return lst_force_refresh.pop(0)
    return None


def force_delayed(value, delay=1):
    # im Zweifesfalle koennen 4-5 Comm cycles dazwischen liegen
    def worker():
        time.sleep(delay)
        lst_force_refresh.append(value)

    t = threading.Thread(target=worker)
    t.start()
    return t  # optional


def handle_set_topic(topic, payload):
    """
    Handle /set topic messages for writable datapoints.
    Topic format: {mqtt_topic}/{dpname}/set
    Converts human-readable values back to write commands.
    """
    try:
        # Extract datapoint name from topic
        # e.g., "vito/c1_temp_room_setpoint/set" -> "c1_temp_room_setpoint"
        topic_parts = topic.split('/')
        if len(topic_parts) < 3 or topic_parts[-1] != 'set':
            logger.warning(f"Invalid /set topic format: {topic}")
            return
        
        dpname = topic_parts[-2]
        value_str = utils.bstr2str(payload).strip()
        
        logger.debug(f"Received /set request: {dpname} = {value_str}")
        
        datapoint_info = poll_list.find_datapoint_by_name(dpname)
        if datapoint_info is None:
            logger.warning(f"/set Datapoint '{dpname}' not found in poll_list")
            return
        
        if datapoint_info['bbfilter']:
            logger.warning(f"/set not possible with bb-filter datapoint '{dpname}'")
            return

        # datapoint_info: (Name, DpAddr, Len, Scale/Type, Signed) or with PollCycle
        addr = datapoint_info['addr']
        length = datapoint_info['len']
        scale_type = datapoint_info.get('scale_type')
        signed = datapoint_info.get('signed', False)
        list_index = datapoint_info['list_index']
        
        # Convert value to bytes
        byte_value = convert_value_to_bytes(value_str, length, scale_type, signed)
        if byte_value is None:
            logger.error(f"Failed to convert value '{value_str}' for datapoint '{dpname}'")
            return
        
        # Create write command in the format: write;addr;len;value
        # For multi-byte values, we need to convert to integer
        int_value = int.from_bytes(byte_value, byteorder='little', signed=signed)
        write_cmd = f"write;{addr:#x};{length};{int_value}"
        
        logger.debug(f"Generated write command: {write_cmd}")
        cmnd_queue.append(write_cmd)

        # Ensure the affected datapoint will be refreshed quite soon
        force_delayed(list_index)

    except Exception as e:
        logger.error(f"Error handling /set topic '{topic}': {e}")


def convert_value_to_bytes(value_str, length, scale_type, signed):
    """
    Convert human-readable value string to bytes for writing.
    Reverse operation of requests_util.get_value()
    """
    try:
        # Handle different format types
        scale_type_str = str(scale_type).lower() if scale_type else ''
        
        # Boolean types   
        if scale_type_str in ('bool', 'boolinv', 'onoff', 'offon'): 
            # Parse boolean-like values
            value_upper = value_str.upper()
            is_true = value_upper in ('1', 'TRUE', 'ON', 'YES')
            is_false = value_upper in ('0', 'FALSE', 'OFF', 'NO')
            
            if not (is_true or is_false):
                logger.warning(f"Invalid boolean value: {value_str}")         #TODO make other nummerical values possibble
                return None
            
            # Apply inverse logic
            if scale_type_str in ('boolinv', 'offon'): 
                bool_val = is_false  # inverted
            else:
                bool_val = is_true
            
            int_val = 1 if bool_val else 0                                     # ATTENTION! True may be anything except 0!!
            return int_val.to_bytes(length, byteorder='little', signed=False)
        
        # Numeric types with scaling
        scale = utils.to_number(scale_type)
        if scale is not None:
            # Parse numeric value and reverse scaling
            float_val = float(value_str)
            int_val = int(round(float_val / scale))
            return int_val.to_bytes(length, byteorder='little', signed=signed)
        
        # String types - not typically writable, but handle anyway
        if scale_type_str in ('utf8', 'utf16'):
            logger.warning(f"String types not typically writable: {scale_type_str}")
            return None
        
        # Default: treat as raw integer
        int_val = utils.get_int(value_str)
        return int_val.to_bytes(length, byteorder='little', signed=signed)
        
    except Exception as e:
        logger.error(f"Error converting value '{value_str}' with scale_type '{scale_type}': {e}")
        return None


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

