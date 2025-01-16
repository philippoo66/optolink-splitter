# "mqtt_base_topic": topic that is read from the optolink-splitter
# "mqtt_discovery_topic": topic that home assistant is listening to for mqtt discovery
# "dp_prefix": added to object_id" and "unique_id" in value of the entity config
#
# MQTT publishing in Homeassistant:
# Home Assitance MQTT discovery description: https://www.home-assistant.io/integrations/mqtt#mqtt-discovery
#    Topic: 
#    {mqtt_discovery_topic}/[domain]/{dp_prefix}{mqtt_base_topic}/config
#    Value:
#    {"object_id": "{dp_prefix}{name}", "unique_id": "{dp_prefix}[name(converted)]", "device": [...] , "availability_topic": "{mqtt_base_topic}/LWT", "state_topic": "{mqtt_base_topic}/[name(converted)]", "name": "[name]", [...]}

import json
import re
import mqtt_util
import time

def Create_Entities():
    with open("entities.json") as js:
        ha_ent = json.load(js)
        js.close()
    mqtt_util.connect_mqtt()
    
    mqtt_base_topic = ha_ent.get("mqtt_base_topic", "")
    mqtt_discovery_topic = ha_ent.get("mqtt_discovery_topic", "")
    dp_prefix = ha_ent.get("dp_prefix", "")
    
    ## Print out all prefix information
    print(f"\nPrefix information \n  mqtt_base_topic: {mqtt_base_topic} \n  mqtt_discovery_topic: {mqtt_discovery_topic} \n  dp_prefix: {dp_prefix}")
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
            "availability_topic": ha_ent['mqtt_base_topic'] + "LWT"
        }
        
        if entity["domain"] != "climate":
            config["state_topic"] = ha_ent["mqtt_base_topic"] + id
        
        for key, value in entity.items():
            if key != "domain":
                if key.endswith("_topic"):
                    config[key] = ha_ent["mqtt_base_topic"] + value
                else:
                    config[key] = value

        
        ## MQTT-Publishing
        mqtt_util.mqtt_client.publish(
            f"{mqtt_discovery_topic}/{entity['domain']}/{ha_ent['dp_prefix']}{id}/config",
            json.dumps(config),
            retain=True,
        )
        
        print(f"Processed entity: {entity['name']}")
        print(f"{mqtt_discovery_topic}/{entity['domain']}/{ha_ent['dp_prefix']}{id}/config")
#        print(json.dumps(config))
        
#        time.sleep(3) ## Uncomment only if necessary: Might be necessary to give HA some time to process the message before the next message arrives. Can lead to MQTT disconnects and entities not being created.
   
if __name__ == "__main__":
    Create_Entities()
