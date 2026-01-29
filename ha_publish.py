'''
   Copyright 2026 matthias-oe

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


   MQTT publishing in Home Assistant:
   --------------------------------------------------
   Home Assistance MQTT discovery description: https://www.home-assistant.io/integrations/mqtt#mqtt-discovery
   Topic:
   {mqtt_ha_discovery_prefix}/[component (e.g. sensor)]/{mqtt_ha_node_id} (OPTIONAL}/{mqtt_optolink_base_topic}/config
   Value:
   {"default_entity_id": "[domain].{dp_prefix}[name][_{address_hex} if dp_suffix_address]",
    "unique_id": "{dp_prefix}[name][_{address_hex} if dp_suffix_address]",
    "state_topic": "{mqtt_base}/[name][_{address_hex} if dp_suffix_address]",
    "device": [...],
    "availability_topic": "{mqtt_optolink_base_topic}/LWT",
    "name": "[name(beautified)]",
    ...}

'''

import json
import paho.mqtt.client as paho
import time
import ssl
from copy import deepcopy

from c_settings_adapter import settings
from ha_shared_config import shared_config

def connect_mqtt(retries=3, delay=5):
    mqtt_client = paho.Client(
        paho.CallbackAPIVersion.VERSION2,
        "datapoints_" + str(int(time.time() * 1000)),
    )

    try:
        # MQTT broker and port
        mqtt_credentials = settings.mqtt_broker.split(":")
        MQTT_BROKER, MQTT_PORT = mqtt_credentials[0], int(mqtt_credentials[1])

        # MQTT authentication (optional)
        mqtt_user_pass = settings.mqtt_user
        if mqtt_user_pass and str(mqtt_user_pass).lower() != "none":
            mqtt_user, mqtt_password = str(mqtt_user_pass).split(":", 1)
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
            print(f"Connecting as {mqtt_user} to MQTT broker {MQTT_BROKER}:{MQTT_PORT}.")
        else:
            print(f"Connecting anonymously to MQTT broker {MQTT_BROKER}:{MQTT_PORT}.")

        # TLS / SSL configuration (optional)
        if settings.mqtt_tls_enable:
            # Skip certificate verification (INSECURE, for testing only)
            skip = bool(settings.mqtt_tls_skip_verify)

            # CA certificate path (None = use OS default CA store)
            ca_path = settings.mqtt_tls_ca_certs

            # Client certificate & key for mutual TLS (optional)
            certfile = settings.mqtt_tls_certfile
            keyfile = settings.mqtt_tls_keyfile

            # Validate mTLS configuration
            if (certfile is not None and keyfile is None) or (keyfile is not None and certfile is None):
                raise Exception("For mTLS you must set mqtt_tls_certfile AND mqtt_tls_keyfile")

            mqtt_client.tls_set(
                ca_certs=ca_path,
                certfile=certfile,
                keyfile=keyfile,
                cert_reqs=(ssl.CERT_NONE if skip else ssl.CERT_REQUIRED),
                tls_version=getattr(ssl, "PROTOCOL_TLS_CLIENT", ssl.PROTOCOL_TLS),
            )

            # Allow insecure connections (e.g. hostname mismatch or skipped verification)
            mqtt_client.tls_insecure_set(skip)

        # Connect with retry logic
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
        
def expand_domain_groups(domains: dict) -> dict:
    """
      eliminate group inside domains and create a separate domain per group
      The generated domain contains all attributes of the original domain, 
      supplemented with the attributes of the group. If the group contains 
      an attribute of the domain, the domain attribute will be overridden.
    """

    new_domains = []
    for dom in shared_config.get("domains", []):
        groups = dom.get("groups")
        if not groups:
            new_domains.append(deepcopy(dom))
            continue
        base = {k: v for k, v in dom.items() if k != "groups"}
        for group in groups:
            merged = deepcopy(base)
            merged.update(group)
            new_domains.append(merged)
    #print(json.dumps(new_domains, indent=2, ensure_ascii=False))
    return new_domains

def beautify(text):
    result = text
    if "beautifier" in shared_config:
        beautifier = shared_config["beautifier"]
        if "search" in beautifier and "replace" in beautifier:
            sea = shared_config["beautifier"]["search"]
            rep = shared_config["beautifier"]["replace"]
            i = 0
            while i < len(sea):
                result = result.replace(sea[i], rep[i])
                i = i + 1
    return result


def publish_ha_discovery():
    """Publishes Home Assistant MQTT discovery config from the shared_config arrays."""
    # MQTT verbinden und prüfen
    mqtt_client = connect_mqtt()
    if mqtt_client is None:
        print(" ERROR: MQTT connection failed. Exiting.")
        return
        
    mqtt_base = settings.mqtt_topic
    ha_prefix = "homeassistant"

    # Device-Info
    node_id = shared_config["node_id"]
    device = shared_config["device"]

    # ID mechanics (compatible with legacy homeassistant_create_entities.py)
    dp_prefix = shared_config.get("dp_prefix", "")
    dp_suffix_address = bool(shared_config.get("dp_suffix_address", True))

    # --- unified helpers for prefix/suffix mechanics ---
    def dp_address_suffix(address_hex: str) -> str:
        return f"_{address_hex}" if dp_suffix_address else ""

    def dp_full_id(name: str, address_hex: str) -> str:
        # used for unique_id + default_entity_id + discovery topic path
        return f"{dp_prefix}{name}{dp_address_suffix(address_hex)}"

    def dp_state_topic(mqtt_base_: str, name: str, address_hex: str) -> str:
        # keep name unprefixed (like before), but suffix consistent
        return f"{mqtt_base_}/{name}{dp_address_suffix(address_hex)}"

    total_published = 0

    for domain_config in expand_domain_groups(shared_config.get("domains", [])):
        domain = domain_config["domain"]

        # Domain-Config bereinigen
        domain_config_clean = domain_config.copy()
        domain_config_clean.pop("poll", None)
        domain_config_clean.pop("nopoll", None)
        domain_config_clean.pop("domain", None)

        poll_items = domain_config.get("poll", [])
        nopoll_items = domain_config.get("nopoll", [])
        all_items = poll_items + nopoll_items

        for item in all_items:
            address_hex = f"0x{item[2]:04x}"
            byte_length = item[3] if len(item) > 3 else 1

            name_converted = item[1]
            id_full = dp_full_id(name_converted, address_hex)

            discovery_config = {
                "name": beautify(item[1].replace("_", " ")).title(),
                "unique_id": id_full,
                "default_entity_id": f"{domain}.{id_full}",
                # BREAKING CHANGE when dp_suffix_address=True: suffix is now part of state_topic as well
                "state_topic": dp_state_topic(mqtt_base, item[1], address_hex),
                "device": device,
                "availability_topic": f"{mqtt_base}/LWT",
            }

            # Domain-Config mergen
            discovery_config.update(domain_config_clean)

            # replace placeholders in '*_template' Entries
            for key, value in list(discovery_config.items()):
                if key.endswith("_template") and isinstance(value, str):
                    if "command_topic" not in discovery_config:
                        discovery_config["command_topic"] = settings.mqtt_listen
                    discovery_config[key] = (
                        value.replace("%address%", address_hex).replace("%bytelength%", str(byte_length))
                    )

            # Publish
            topic = f"{ha_prefix}/{domain}/{node_id}/{discovery_config['unique_id']}/config"
            mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
            print(
                f"Published {domain}: {discovery_config['name']} ({address_hex}) -> {discovery_config['unique_id']}"
            )
            total_published += 1
            time.sleep(0.1)  # Rate limiting

    # Commands (no address -> prefix only, no address-suffix)
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
        mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
        print(f"Published {domain}: {discovery_config['name']} -> {discovery_config['unique_id']}")
        total_published += 1
        time.sleep(0.1)  # Rate limiting

    print(f"\n✓ {total_published} entities published successfully!")

    # Graceful shutdown
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


if __name__ == "__main__":
    publish_ha_discovery()
