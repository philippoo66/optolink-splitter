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

import time
import paho.mqtt.client as paho

from optolink_splitter.config_model import SplitterConfig
from optolink_splitter.utils.common_utils import bstr2str


verbose = False
mqtt_client = None
cmnd_queue = []  # command queue to serialize bus traffic


def on_connect(client, userdata, flags, reason_code, properties):
    if userdata != None:
        client.subscribe(userdata)


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print("mqtt broker disconnected. reason_code = " + str(reason_code))


def on_message(client, userdata, msg):
    # print("MQTT recd:", msg.topic, msg.payload)
    if userdata is None:
        print("MQTT recd:", msg.topic, msg.payload)  # ErrMsg oder so?
        return
    topic = str(msg.topic)  # Topic in String umwandeln
    if topic == userdata:
        rec = bstr2str(msg.payload)
        rec = (
            rec.replace(" ", "")
            .replace("\0", "")
            .replace("\n", "")
            .replace("\r", "")
            .replace('"', "")
            .replace("'", "")
        )
        cmnd_queue.append(rec)


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")


def connect_mqtt(config: SplitterConfig):
    global mqtt_client
    try:
        # Verbindung zu MQTT Broker herstellen ++++++++++++++
        mqtt_client = paho.Client(
            paho.CallbackAPIVersion.VERSION2,
            "OLswitch" + "_" + str(int(time.time() * 1000)),
            userdata=config.mqtt_listen_address,
        )  # Unique mqtt id using timestamp
        if config.mqtt_user is not None:
            mlst = config.mqtt_user.split(":")
            mqtt_client.username_pw_set(mlst[0], password=mlst[1])
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        if config.mqtt_listen_address is not None:
            mqtt_client.on_subscribe = on_subscribe
        mlst = config.mqtt_address.split(":")
        mqtt_client.connect(mlst[0], int(mlst[1]))
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
        mqtt_client.loop_start()
        # preparations
        if config.mqtt_fstr is None:
            config.mqtt_fstr = "{dpname}"
    except Exception as e:
        raise Exception("Error connecting MQTT: " + str(e))


def get_mqtt_request() -> str:
    ret = ""
    if len(cmnd_queue) > 0:
        ret = cmnd_queue.pop(0)
    return ret


def publish_read(config: SplitterConfig, name, addr, value):
    if mqtt_client != None:
        publishStr = config.mqtt_fstr.format(dpaddr=addr, dpname=name)
        # send
        ret = mqtt_client.publish(config.mqtt_topic + "/" + publishStr, value)
        if verbose:
            print(ret)


def publish_response(config: SplitterConfig, resp: str):
    if mqtt_client != None:
        ret = mqtt_client.publish(config.mqtt_respond_address, resp)
        if verbose:
            print(ret)


def exit_mqtt():
    if mqtt_client != None:
        print("disconnect MQTT client")
        mqtt_client.disconnect()


# ------------------------
# main for test only
# ------------------------
def main():
    try:
        connect_mqtt()
        print("connect ok")
        while True:
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
