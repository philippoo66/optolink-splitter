# This script is designed to make Optolink-Splitter datapoints available in Home Assistant by publishing them via MQTT. 
# The configuration is defined in the homeassistant_entities.json file.
#
# MQTT publishing in Homeassistant:
# --------------------------------------------------
#  Home Assistance MQTT discovery description: https://www.home-assistant.io/integrations/mqtt#mqtt-discovery
#   Topic: 
#    {mqtt_ha_discovery_prefix}/[component (e.g. sensor)]/{mqtt_ha_node_id} (OPTIONAL}/{mqtt_optolink_base_topic}/config
#   Value:
#    {"object_id": "{dp_prefix}{name}", "unique_id": "{dp_prefix}[name(converted)]", "device": [...] , "availability_topic": "{mqtt_optolink_base_topic}/LWT", "state_topic": "{mqtt_optolink_base_topic}/[name(converted)]", "name": "[name]", [...]}
#
# homeassistant_entities.json file values
# --------------------------------------------------
#  "mqtt_optolink_base_topic": Topic read from the optolink-splitter. The value must end with a "/", e.g. "vitocal/".
#  "mqtt_ha_discovery_prefix": Topic Home Assistant listens to for MQTT discovery. Home Assistants default is "homeassistant".
#  "mqtt_ha_node_id" (optional): Not necessarily needed by Home Assistant. Can be used to structure the MQTT topic — see the example of publishing below. The value must end with a "/" or be empty if not used. 
#  "dp_prefix": Added to "object_id" and "unique_id" in the value of the entity configuration. The value should end with an "_", e.g., "vitocal_".

import json
import re
import mqtt_util
import time

def Create_Entities():
    with open("homeassistant_entities.json") as js:
        ha_ent = json.load(js)
        js.close()
    mqtt_util.connect_mqtt()
    mqtt_optolink_base_topic = ha_ent.get("mqtt_optolink_base_topic", "")
    mqtt_ha_discovery_prefix = ha_ent.get("mqtt_ha_discovery_prefix", "")
    mqtt_ha_node_id = ha_ent.get("mqtt_ha_node_id", "")
    dp_prefix = ha_ent.get("dp_prefix", "")
    
    ## Print out all prefix information
    print(f"\nPrefix information \n  mqtt_optolink_base_topic: {mqtt_optolink_base_topic} \n  mqtt_ha_discovery_prefix: {mqtt_ha_discovery_prefix} \n  mqtt_ha_node_id: {mqtt_ha_node_id} \n  dp_prefix: {dp_prefix}")
    ## Print out all datapoints and their name conversions
    print("\nAll generated IDs from Entities")
    for entity in ha_ent["datapoints"]:
        id = re.sub(r"[^0-9a-zA-Z]+", "_", entity["name"]).lower()
        print(f"  ID: {id} / Entity: {entity['name']}")
    print("\n\n")
     
    for entity in ha_ent["datapoints"]:
        id = re.sub(r"[^0-9a-zA-Z]+", "_", entity["name"]).lower()
        config = {
            "object_id": ha_ent["dp_prefix"] + id,
            "unique_id": ha_ent["dp_prefix"] + id,
            "device": ha_ent["device"],
            "availability_topic": ha_ent['mqtt_optolink_base_topic'] + "LWT"
        }
        
        if entity["domain"] != "climate":
            config["state_topic"] = ha_ent["mqtt_optolink_base_topic"] + id
        
        for key, value in entity.items():
            if key != "domain":
                if key.endswith("_topic"):
                    config[key] = ha_ent["mqtt_optolink_base_topic"] + value
                else:
                    config[key] = value

        
        ## MQTT-Publishing
        mqtt_util.mqtt_client.publish(
            f"{mqtt_ha_discovery_prefix}/{entity['domain']}/{ha_ent['mqtt_ha_node_id']}{id}/config",
            json.dumps(config),
            retain=True,
        )
        
        print(f"Processed entity: {entity['name']}")
        print(f"   {mqtt_ha_discovery_prefix}/{entity['domain']}/{ha_ent['mqtt_ha_node_id']}{id}/config")
        print(json.dumps(config))
        print("\n")
        
#        time.sleep(3) ## Uncomment only if necessary: Might be necessary to give HA some time to process the message before the next message arrives. Can lead to MQTT disconnects and entities not being created.
   
if __name__ == "__main__":
    Create_Entities()
