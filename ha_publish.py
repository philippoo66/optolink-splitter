''' 
   Copyright 2026 matthias-oe
   Contributions by: EarlSneedSinclair

   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   This script is designed to make Optolink-Splitter datapoints available in Home Assistant by publishing them via MQTT.
   The configuration is defined in the ha_shared_config.py file.

   The documentation can be found here:
      https://github.com/philippoo66/optolink-splitter/wiki/211-Alternative-Home-Assistant-Integration
'''

import argparse
import json
import paho.mqtt.client as paho
import time
import ssl
import re
from copy import deepcopy

from c_settings_adapter import settings
from ha_shared_config import shared_config
from ha_shared_config import poll_items

def connect_mqtt(retries=3, delay=5):
    mqtt_client = paho.Client(
        paho.CallbackAPIVersion.VERSION2,
        "datapoints_" + str(int(time.time() * 1000)),
    )

    try:
        mqtt_credentials = settings.mqtt_broker.split(":")
        MQTT_BROKER, MQTT_PORT = mqtt_credentials[0], int(mqtt_credentials[1])

        mqtt_user_pass = settings.mqtt_user
        if mqtt_user_pass and str(mqtt_user_pass).lower() != "none":
            mqtt_user, mqtt_password = str(mqtt_user_pass).split(":", 1)
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
            print(f"Connecting as user {mqtt_user} to MQTT broker {MQTT_BROKER}:{MQTT_PORT}.")
        else:
            print(f"Connecting anonymously to MQTT broker {MQTT_BROKER}:{MQTT_PORT}.")

        if settings.mqtt_tls_enable:
            skip = bool(settings.mqtt_tls_skip_verify)
            ca_path = settings.mqtt_tls_ca_certs
            certfile = settings.mqtt_tls_certfile
            keyfile = settings.mqtt_tls_keyfile

            if (certfile is not None and keyfile is None) or (keyfile is not None and certfile is None):
                raise Exception("For mTLS you must set mqtt_tls_certfile AND mqtt_tls_keyfile")

            mqtt_client.tls_set(
                ca_certs=ca_path,
                certfile=certfile,
                keyfile=keyfile,
                cert_reqs=(ssl.CERT_NONE if skip else ssl.CERT_REQUIRED),
                tls_version=getattr(ssl, "PROTOCOL_TLS_CLIENT", ssl.PROTOCOL_TLS),
            )

            mqtt_client.tls_insecure_set(skip)

        for attempt in range(retries):
            try:
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                mqtt_client.loop_start()
                print(" ✓ MQTT connected successfully.")
                return mqtt_client
            except Exception as retry_error:
                print(f" ERROR: MQTT connection failed (Attempt {attempt+1}/{retries}): {retry_error}")
                time.sleep(delay)

        print(" ERROR: Could not establish MQTT connection after multiple retries.")
        return None

    except Exception as e:
        print(f" ERROR connecting to MQTT broker: {e}")
        return None


def verify_mqtt_optolink_lwt(mqtt_client, mqtt_base, timeout=10):
    if mqtt_client is None:
        print(" ERROR: MQTT client is not initialized.")
        return False

    if mqtt_base is None or str(mqtt_base).strip() == "":
        print(" ERROR: settings.mqtt_topic is not set. Cannot determine Optolink base topic.")
        return False

    LWT_TOPIC = f"{mqtt_base}/LWT"

    try:
        lwt_status = {"online": False}

        def on_message(client, userdata, message):
            payload = message.payload.decode()
            if payload == "online":
                print(" MQTT is connected. Optolink-Splitter LWT reports 'online'.")
                lwt_status["online"] = True

        mqtt_client.on_message = on_message
        print(f"Subscribing to {LWT_TOPIC}...")
        mqtt_client.subscribe(LWT_TOPIC)

        start_time = time.time()
        while time.time() - start_time < timeout:
            if lwt_status["online"]:
                return True
            time.sleep(1)

        print(" ERROR: Optolink-Splitter LWT did not report 'online'.")
        print(" Ensure optolinkvs2_switch.py (or the corresponding service) is running.")
        return False

    except Exception as e:
        print(f" ERROR: Failed to verify Optolink-Splitter LWT: {e}")
        return False


def expand_domain_units(domains: list) -> list:
    """
      eliminate unit inside domains and create a separate domain per unit
      The generated domain contains all attributes of the original domain, 
      supplemented with the attributes of the unit. If the unit contains 
      an attribute of the domain, the domain attribute will be overridden.
    """

    new_domains = []
    for dom in domains:
        units = dom.get("units")
        if not units:
            new_domains.append(deepcopy(dom))
            continue
        base = {k: v for k, v in dom.items() if k != "units"}
        for unit in units:
            merged = deepcopy(base)
            merged.update(unit)
            new_domains.append(merged)
    return new_domains


def beautify(text):
    beautifier = shared_config.get("beautifier", {})
    result = text
    if "search" in beautifier and "replace" in beautifier:
        sea, rep = beautifier["search"], beautifier["replace"]
        for old, new in zip(sea, rep):
            result = result.replace(old, new)
    result = result.title()
    if "fixed" in beautifier:
        fixed = beautifier["fixed"]
        for fix in fixed:
            pattern = re.compile(re.escape(fix), re.IGNORECASE)
            result = pattern.sub(fix, result)
    return result

def to_dpaddr_str(dp_addr) -> str | None:
    if dp_addr is None:
        return None
    if isinstance(dp_addr, int):
        return f"0x{dp_addr:04x}"
    return str(dp_addr)

def extract_poll_params():
    poll_map = {}
    for item in poll_items:
        if isinstance(item, (tuple, list)):
            dp_name = item[1] if len(item) > 1 else ""
            dpaddr_str = to_dpaddr_str(item[2] if len(item) > 2 else None)
            length = item[3] if len(item) > 3 else 1
        else:
            dp_name = item.get("name", "")
            dpaddr_str = to_dpaddr_str(item.get("dpaddr_str"))
            length = item.get("length", 1)
        
        if dp_name and dpaddr_str is not None:
            poll_map[dp_name] = {"DpAddr": dpaddr_str, "Length": str(length)}
    return poll_map

def build_discovery_config(domain, item_config, mqtt_base, dp_prefix, dp_suffix_address, device_config):
    def set_if_missing(cfg: dict, key: str, value) -> None:
        if key not in cfg:
            cfg[key] = value

    def merge_item_dict_set_if_missing(dst: dict, src: dict) -> None:
        for key, value in src.items():
            set_if_missing(dst, key, value)

    def to_name_id(name) -> str:
        return str(name).lower().replace(" ", "_")

    def address_suffix(dpaddr_str):
        return f"_{dpaddr_str}" if (dp_suffix_address and dpaddr_str is not None) else ""

    def make_unique_id(name_id, dpaddr_str):
        return f"{dp_prefix}{name_id}{address_suffix(dpaddr_str)}"

    if isinstance(item_config, (tuple, list)):
        dp_name = item_config[1] if len(item_config) > 1 else "unknown"
        dpaddr_str = to_dpaddr_str(item_config[2] if len(item_config) > 2 else None)
        item_dict = None
    else:
        dp_name = item_config.get("name", "unknown")
        dpaddr_str = to_dpaddr_str(item_config.get("dpaddr_str", None))
        item_dict = item_config

    name_id = to_name_id(dp_name)
    unique_id = make_unique_id(name_id, dpaddr_str)

    discovery_config = {
        "name": beautify(str(dp_name).replace("_", " ")),
        "unique_id": unique_id,
        "default_entity_id": f"{domain}.{unique_id}",
        "device": device_config,
        "availability_topic": f"{mqtt_base}/LWT",
    }

    if item_dict:
        normalized = {}
        for key, value in item_dict.items():
            if isinstance(value, str):
                value = value.replace("{mqtt_base}", mqtt_base)
            normalized[key] = value
        merge_item_dict_set_if_missing(discovery_config, normalized)

    return discovery_config, name_id, dpaddr_str


def publish_ha_discovery():
    parser = argparse.ArgumentParser(
        description="make Optolink-Splitter datapoints available in Home Assistant by publishing them via MQTT"
    )
    parser.add_argument("-c", "--console", dest="console", action="store_true", help="Console Output only")
    args = parser.parse_args()
    if args.console:
        print("Console Output only")

    if not args.console:
        mqtt_client = connect_mqtt()
        if mqtt_client is None:
            print(" ERROR: MQTT connection failed. Exiting.")
            return
        
    mqtt_base = settings.mqtt_topic
    ha_prefix = shared_config.get("discovery_prefix") or "homeassistant"

    if not args.console:
        if not verify_mqtt_optolink_lwt(mqtt_client, mqtt_base):
            print("ERROR: Optolink-Splitter is offline. Exiting script to prevent MQTT discovery issues.")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            return

    node_id = shared_config["node_id"]
    device = shared_config["device"]

    dp_prefix = shared_config.get("dp_prefix", "")
    dp_suffix_address = bool(shared_config.get("dp_suffix_address", True))

    poll_map = extract_poll_params()
    if args.console:
        print(f"{json.dumps(poll_map, indent=2)}")    
    
    total_published = 0

    for domain_config in expand_domain_units(shared_config.get("domains", [])):
        domain = domain_config["domain"]

        domain_config_clean = domain_config.copy()
        domain_config_clean.pop("poll", None)
        domain_config_clean.pop("nopoll", None)
        domain_config_clean.pop("domain", None)

        if "domainname" in domain_config:
            all_items = [{"name": domain_config["domainname"]}]
            domain_config_clean.pop("domainname", None)
        else:
            poll_list = domain_config.get("poll", [])
            nopoll_list = domain_config.get("nopoll", [])
            all_items = poll_list + nopoll_list


        for item in all_items:
            discovery_config, name_id, dpaddr_str = build_discovery_config(
                domain=domain,
                item_config=item,
                mqtt_base=mqtt_base,
                dp_suffix_address=dp_suffix_address,
                device_config=device,
            )
 
            for k, v in domain_config_clean.items():
                if k not in discovery_config:
                    if k.endswith("_topic") and not k.endswith("_command_topic"):
                        e = poll_map.get(v)
                        if e is not None:
                            suffix = f"_{e['DpAddr']}" if (dp_suffix_address) else ""
                            v = f"{mqtt_base}/{v}{suffix}"
                    if k.endswith("_template"):
                        if re.search(r'%[^%]+:[^%]+%', v):
                            for name, params in poll_map.items():
                                v = v.replace(f"%{name}:DpAddr%", params["DpAddr"])
                                v = v.replace(f"%{name}:Length%", params["Length"])
                    discovery_config[k] = v
                 
            if isinstance(item, (tuple, list)):
                length = item[3] if len(item) > 3 else 1
            else:
                length = item.get("length", 1)

            if dpaddr_str is not None:
                for key, value in list(discovery_config.items()):
                    if isinstance(value, str):
                        if "%DpAddr%" in value or "%Length%" in value:
                            discovery_config[key] = (
                                value.replace("%DpAddr%", dpaddr_str)
                                     .replace("%Length%", str(length))
                            )

            if domain != "button":
                has_state_topics = any(k.endswith("_state_topic") for k in discovery_config.keys())
                if "state_topic" not in discovery_config and not has_state_topics:
                    suffix = f"_{dpaddr_str}" if (dp_suffix_address and dpaddr_str is not None) else ""
                    discovery_config["state_topic"] = f"{mqtt_base}/{name_id}{suffix}"

            topic_id = f"{name_id}{(f'_{dpaddr_str}' if (dp_suffix_address and dpaddr_str is not None) else '')}"
            topic = f"{ha_prefix}/{domain}/{node_id}/{topic_id}/config"
            if args.console:
                print(f"{'-'*80}\n{topic}\n{json.dumps(discovery_config, indent=2)}")
            else:
                mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
            print(f"Published {domain}: {discovery_config['name']} -> {discovery_config['unique_id']}")
            total_published += 1
            time.sleep(0.1)

    for command_config in shared_config.get("commands", []):
        domain = "button"

        command_config_clean = command_config.copy()
        command_name = command_config_clean.pop("name")

        cmd_id = f"{dp_prefix}command_{command_name}"

        discovery_config = {
            "name": beautify(command_name.replace("_", " ")).title(),
            "unique_id": cmd_id,
            "default_entity_id": f"{domain}.{cmd_id}",
            "command_topic": settings.mqtt_listen,
            "device": device,
        }

        discovery_config.update(command_config_clean)

        topic = f"{ha_prefix}/{domain}/{node_id}/{discovery_config['unique_id']}/config"
        if args.console:
            print(f"{'-'*80}\n{topic}\n{json.dumps(discovery_config, indent=2)}")
        else:
            mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
        print(f"Published {domain}: {discovery_config['name']} -> {discovery_config['unique_id']}")
        total_published += 1
        if not args.console:
            time.sleep(0.1)  # Rate limiting

    print(f"\n✓ {total_published} entities published successfully!")

    # Graceful shutdown
    if not args.console:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    publish_ha_discovery()
