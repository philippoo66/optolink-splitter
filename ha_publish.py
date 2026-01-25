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
   {"object_id": "{dp_prefix}{name}", "unique_id": "{dp_prefix}[name(converted)]", "device": [...] , "availability_topic": "{mqtt_optolink_base_topic}/LWT", "state_topic": "{mqtt_optolink_base_topic}/[name(converted)]", "name": "[name]", [...]}
   
'''

import json
import importlib
import time

from c_settings_adapter import settings

from ha_shared_config import shared_config

# Global MQTT Client
mod_mqtt_util = None

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
    """Veröffentlicht HA Discovery mit neuer Array-Struktur."""
    global mod_mqtt_util

    # MQTT verbinden und prüfen
    mod_mqtt_util = importlib.import_module("mqtt_util")
    mod_mqtt_util.connect_mqtt()
    if (mod_mqtt_util is None) or (not mod_mqtt_util.mqtt_client.is_connected):
        print(" ERROR: MQTT connection failed. Exiting.")
        return

    mqtt_base = settings.mqtt_topic
    ha_prefix = "homeassistant"
    
    # Device-Info
    node_id = shared_config["node_id"]
    device = shared_config["device"]
    
    total_published = 0
    
    for domain_config in shared_config["domains"]:
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
            
            discovery_config = {
                "name" : beautify(item[1].replace("_", " ")).title(),
                "unique_id": f"{item[1]}_{address_hex}",
                "state_topic": f"{mqtt_base}/{item[1]}",
                "device": device,
                "availability_topic": f"{mqtt_base}/LWT"
            }
            
            # Domain-Config mergen
            discovery_config.update(domain_config_clean)
            
            # replace placeholders in '*_template' Entries
            for key, value in list(discovery_config.items()):
                if key.endswith("_template") and isinstance(value, str):
                    if "command_topic" not in discovery_config:
                        discovery_config["command_topic"] = settings.mqtt_listen
                    discovery_config[key] = (
                        value.replace("%address%", address_hex)
                             .replace("%bytelength%", str(byte_length))
                    )
            # print (json.dumps(discovery_config))
            # Publish
            topic = f"{ha_prefix}/{domain}/{node_id}/{discovery_config['unique_id']}/config"
            mod_mqtt_util.mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
            print(f"Published {domain}: {discovery_config['name']} ({address_hex}) -> {discovery_config['unique_id']}")
            total_published += 1
            time.sleep(0.1)  # Rate limiting

    for command_config in shared_config["commands"]: 
        domain = "button"
        # Domain-Config bereinigen
        command_config_clean = command_config.copy()
        command_config_clean.pop("name", None)
        discovery_config = {
            "name" : beautify(command_config["name"].replace("_", " ")).title(),
            "unique_id": f"command_{command_config["name"]}",
            "command_topic" : settings.mqtt_listen,
            "device": device
        }
        discovery_config.update(command_config_clean)
            
        #print (json.dumps(discovery_config))
        # Publish
        topic = f"{ha_prefix}/{domain}/{node_id}/{discovery_config['unique_id']}/config"
        mod_mqtt_util.mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
        print(f"Published {domain}: {discovery_config['name']} -> {discovery_config['unique_id']}")
        total_published += 1
        time.sleep(0.1)  # Rate limiting
    
    print(f"\n✓ {total_published} entities published successfully!")
    
    # Graceful shutdown
    mod_mqtt_util.mqtt_client.loop_stop()
    mod_mqtt_util.mqtt_client.disconnect()

if __name__ == "__main__":
    publish_ha_discovery()
