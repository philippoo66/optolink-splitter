# This script is designed to make Optolink-Splitter datapoints available in Home Assistant by publishing them via MQTT. 
# The configuration is defined in the homeassistant_entities.json file.
#
# Important Note:
# Home Assistant will ignore MQTT discovery messages if the Optolink-Splitter is offline (LWT != 'online').
# This means that new entities will not be created, and existing ones may not be updated correctly.
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
#  "mqtt_ha_node_id" (optional): Not necessarily needed by Home Assistant. Can be used to structure the MQTT topic, see the example of publishing above. The value must end with a "/" or be empty if not used. 
#  "dp_prefix": Added to "object_id" and "unique_id" in the value of the entity configuration. The value should end with an "_", e.g., "vitocal_".

import json
import re
import time
import sys
import paho.mqtt.client as paho
from c_settings_adapter import settings

import c_polllist

# Global MQTT Client
mqtt_client = None

def connect_mqtt(retries=3, delay=5):
    """ Global MQTT Client for this script. 
        Connects to the MQTT broker using credentials from settings.py """

    global mqtt_client

    if mqtt_client is None:
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, "ha_entities_" + str(int(time.time()*1000)))

    if mqtt_client.is_connected():
        print(" MQTT client is already connected. Skipping reconnection.")
        return True

    try:
        mqtt_credentials = settings.mqtt_broker.split(':')
        if len(mqtt_credentials) != 2:
            raise ValueError("ERROR: MQTT settings must be in the format 'host:port'")

        MQTT_BROKER, MQTT_PORT = mqtt_credentials[0], int(mqtt_credentials[1])

        mqtt_user_pass = settings.mqtt_user
        if mqtt_user_pass and mqtt_user_pass.lower() != "none":
            mqtt_user, mqtt_password = mqtt_user_pass.split(":")
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
            print(f"Connecting as {mqtt_user} to MQTT broker {MQTT_BROKER} on port {MQTT_PORT}...")
        else:
            print(f"Connecting anonymously to MQTT broker {MQTT_BROKER} on port {MQTT_PORT}...")

        for attempt in range(retries):
            try:
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                mqtt_client.loop_start()
                print(" MQTT connected successfully.")
                return True
            except Exception as retry_error:
                print(f" ERROR: MQTT connection failed (Attempt {attempt+1}/{retries}): {retry_error}")
                time.sleep(delay)

        print(" ERROR: Could not establish an MQTT connection after multiple retries.")
        return False

    except Exception as e:
        print(f" ERROR connecting to MQTT broker: {e}")
        return False  # Explicitly return failure


def verify_mqtt_optolink_lwt(timeout=10):
    """ Verifies the availability of the Optolink-Splitter via LWT topic. """

    global mqtt_client

    if mqtt_client is None:
        print(" ERROR: MQTT client is not initialized.")
        return False

    try:
        with open("homeassistant_entities.json") as json_file:
            ha_ent = json.load(json_file)

        mqtt_optolink_base_topic = ha_ent.get("mqtt_optolink_base_topic", "")
        LWT_TOPIC = f"{mqtt_optolink_base_topic}LWT"

        lwt_status = {"online": False}  # Dictionary to store LWT status

        def on_message(client, userdata, message):
            payload = message.payload.decode()
            if payload == "online":
                print(f" MQTT is connected. Optolink-Splitter LWT reports 'online'.")
                lwt_status["online"] = True

        mqtt_client.on_message = on_message # Assign the callback to the existing mqtt_client
        print(f"Subscribing to {LWT_TOPIC}...")
        mqtt_client.subscribe(LWT_TOPIC)

        start_time = time.monotonic()
        while time.monotonic() < start_time + timeout:
            if lwt_status["online"]:
                return True
            time.sleep(1)

        print(" ERROR: Optolink-Splitter LWT did not report 'online'.")
        print(" Ensure optolinkvs2_switch.py (or the corresponding service) is running.")
        return False

    except Exception as e:
        print(f" ERROR verifying MQTT Optolink LWT: {e}")
        return False  # Return failure instead of exiting

def read_poll_list_datapoints():
    """ Reads the poll_list either from settings.py or poll_list.py using c_polllist. """
    
    poll_list_datapoints = []

    try:
        poll_items = c_polllist.poll_list.items
        print(f"Reading poll_list from poll_list.py or settings.py")
        for item in poll_items:
            if len(item) > 1:
                # # Checks if the first value is PollCycle (an integer). If so, it takes the next value as the name.
                # if isinstance(item[0], int):
                name = item[1]  # since 1.10.6 always item[0] is PollCycleGroupKey
                # else:
                #     name = item[0]  # If first value is not an integer, it's the name

                poll_list_datapoints.append(name)
    except Exception as e:
        print(f"Error reading poll list datapoints: {e}")

    return poll_list_datapoints


def read_homeassistant_entities():
    """ Reads the entities to be created in Home Assistant from homeassistant_entities.json. """

    try:
        print("Reading homeassistant_entities from homeassistant_entities.json")
        with open("homeassistant_entities.json") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(" ERROR: homeassistant_entities.json not found.")
    except json.JSONDecodeError:
        print(" ERROR: homeassistant_entities.json contains invalid JSON.")
    except Exception as e:
        print(f" ERROR: Unexpected issue while reading homeassistant_entities.json: {e}")
    
    return None

def transform_and_check_datapoints(homeassistant_entities, poll_list):
    """ Transforms the entities into generated datapoints (e.g., removing special characters and converting to lowercase). """

    if homeassistant_entities is None:
        print(" ERROR: No Home Assistant entities available. Cannot proceed with transformation.")
        return None, None, None  # Return empty values so the script does not continue with invalid data

    print("\n\nList of generated datapoint IDs (settings_ini), created from HA entities (homeassistant_entities.json):\n")

    entity_count_per_domain = {}
    entity_data = []

    # Convert poll_list to a set for faster lookup
    poll_list_set = set(poll_list)

    # Collect entity data
    for entity in homeassistant_entities.get("datapoints", []):
        entity_id = re.sub(r"[^0-9a-zA-Z]+", "_", entity["name"]).lower()
        entity_domain = entity.get("domain", "unknown")

        # Check if the generated datapoint exists in the poll list
        found_in_poll_list = "Yes" if entity_id in poll_list_set else "No"

        # Track entity counts per domain
        entity_count_per_domain[entity_domain] = entity_count_per_domain.get(entity_domain, 0) + 1

        # Store entity data
        entity_data.append((entity["name"], entity_domain, entity_id, found_in_poll_list, ""))

    check_entities_and_print_entity_table(entity_data)

    return homeassistant_entities, entity_count_per_domain, entity_data


def check_entities_and_print_entity_table(entity_data):
    """ Checks if entities from homeassistant_entities.json are found in poll_items and prints a summary table of all entities. 
        A warning is thrown if any entities are not found in poll_items. """
        
    # Sort entity data by Domain for grouping
    entity_data.sort(key=lambda x: x[1])  # x[1] is the Domain column

    # Count entities per domain
    domain_counts = {}
    for _, entity_domain, _, _, _ in entity_data:
        domain_counts[entity_domain] = domain_counts.get(entity_domain, 0) + 1

    # Check if any entity was not found in poll_list
    missing_poll_items = any(found == "No" for _, _, _, found, _ in entity_data)

    # Determine column widths dynamically
    max_domain_length = max(len("Domain"), max(len(e[1]) for e in entity_data))  # Keep header width
    max_name_length = max(len("HA-Entity from json"), max(len(e[0]) for e in entity_data))  # HA-Entity from JSON
    max_id_length = max(len("Datapoint (DP)"), max(len(e[2]) for e in entity_data))  # Generated Datapoint
    max_poll_length = max(len("in poll_list?"), len("Yes"))  # Static length for the second row header

    # Set proper spacing for headers (first row)
    header_1 = (
        " " * max_domain_length + " | "
        + " " * max_name_length + " | "
        + "Generated".ljust(max_id_length) + " | "
        + "DP found".ljust(max_poll_length)
    )

    # Second row of headers (column names)
    header_2 = (
        "Domain".ljust(max_domain_length) + " | "
        + "HA-Entity from json".ljust(max_name_length) + " | "
        + "Datapoint (DP)".ljust(max_id_length) + " | "
        + "in poll_list?".ljust(max_poll_length)
    )

    # Print table headers
    print(header_1)
    print(header_2)

    # Track the current domain to group entities
    current_domain = None
    total_entities = 0

    # Print each entity row with correct column order
    for entity_name, entity_domain, entity_id, found_in_poll_list, _ in entity_data:
        # If a new domain starts, add a compact inline domain header
        if entity_domain != current_domain:
            current_domain = entity_domain  # Update current domain
            
            # Print domain header inline with the divider
            domain_header = f"{entity_domain} ({domain_counts[entity_domain]}) "
            divider_length = (
                max_domain_length + max_name_length + max_id_length + max_poll_length + 9 - len(domain_header)
            )
            print(domain_header + "-" * divider_length)

        # Empty domain value in rows
        print(
            f"{' '.ljust(max_domain_length)} | "
            f"{entity_name.ljust(max_name_length)} | "
            f"{entity_id.ljust(max_id_length)} | "
            f"{found_in_poll_list.ljust(max_poll_length)}"
        )

        total_entities += 1

    # Final divider and total count
    print("-" * (max_domain_length + max_name_length + max_id_length + max_poll_length + 9))
    print(f"TOTAL ENTITIES: {total_entities}\n")

    # Display a warning if any generated datapoint (DP) does not exist in poll_items.
    if missing_poll_items:
        print("\n" * 4 + "!!! WARNING !!!")
        print("One or more entities from your homeassistant_entities.json were not found in your poll_items (settings.py or poll_list.py).")

        print("\nPossible causes:")
        print(" - Thermostats consist of multiple values with no direct counterpart in poll_items.")
        print(" - Switches consist of multiple values with no direct counterpart in poll_items.")
        print(' - "Cmnd" refers to commands sent from Home Assistant to the Optolink-Splitter, and therefore has no direct counterpart in poll_items.')
        print(' - "Resp" is the response to commands sent by the Optolink-Splitter, and therefore has no direct counterpart in poll_items.\n')


        print("For other entities, especially SENSORs, this could be critical, as they will not attach to a value and will not be displayed in Home Assistant.\n")
        
        print("To prevent this issue, PLEASE CHECK SPELLING AND ENSURE THAT POLL_ITEMS ARE IN LOWERCASE.")
        print("Recommendation: Keep all MQTT-related values (e.g. mqtt_topic) in lowercase!\n")

        print("\n" * 4 + "Continuing script...\n")

    time.sleep(3)
    
def publish_homeassistant_entities():
    """ Assembles MQTT topics and values, then publishes MQTT messages to Home Assistant Discovery. """

    # Read Home Assistant entities
    homeassistant_entities = read_homeassistant_entities()
    if homeassistant_entities is None:
        print(" ERROR: Could not load homeassistant_entities.json. Exiting script to prevent invalid MQTT discovery messages.")
        sys.exit(1)  # Exit cleanly to avoid undefined behavior

    # Fetch poll_list
    poll_list = read_poll_list_datapoints()
    if poll_list is None:
        print(" ERROR: Poll list could not be loaded. Exiting script to prevent invalid MQTT discovery messages.")
        sys.exit(1)

    # Prepare and validate entities
    homeassistant_entities, entity_count_per_domain, entity_data = transform_and_check_datapoints(homeassistant_entities, poll_list)

    # Ensure MQTT connection is established before publishing
    if not connect_mqtt():
        print(" ERROR: Unable to establish MQTT connection. Exiting.")
        sys.exit(1)

    # Check if Optolink-Splitter is online before proceeding
    if not verify_mqtt_optolink_lwt():
        print("ERROR: Optolink-Splitter is offline. Exiting script to prevent MQTT discovery issues.")
        sys.exit(1)

    print("\nPublishing entities now...\n")

    # Extract necessary MQTT parameters
    mqtt_optolink_base_topic = homeassistant_entities.get("mqtt_optolink_base_topic", "")
    mqtt_ha_discovery_prefix = homeassistant_entities.get("mqtt_ha_discovery_prefix", "")
    mqtt_ha_node_id = homeassistant_entities.get("mqtt_ha_node_id", "")
    dp_prefix = homeassistant_entities.get("dp_prefix", "")

    # Print summary of found entities
    print("MQTT Topic & Publishing Settings:\n" +
          f" mqtt_optolink_base_topic:\t{mqtt_optolink_base_topic}\n" +
          f" mqtt_ha_discovery_prefix:\t{mqtt_ha_discovery_prefix}\n" +
          f" mqtt_ha_node_id:\t\t{mqtt_ha_node_id}\n" +
          f" dp_prefix:\t\t\t{dp_prefix}\n")

    # Initialize publishing counter
    total_entities = len(entity_data)

    # Iterate over all entities and count while publishing
    for count, (entity_name, entity_domain, entity_id, _, _) in enumerate(entity_data, start=1):
        # Construct MQTT discovery message payload
        config = {
            "object_id": dp_prefix + entity_id,
            "unique_id": dp_prefix + entity_id,
            "device": homeassistant_entities["device"],
            "availability_topic": mqtt_optolink_base_topic + "LWT"
        }

        # Ensure the correct state topic
        if entity_domain != "climate":
            config["state_topic"] = mqtt_optolink_base_topic + entity_id

        # Find the correct entity in homeassistant_entities["datapoints"]
        current_entity = next((e for e in homeassistant_entities["datapoints"] if re.sub(r"[^0-9a-zA-Z]+", "_", e["name"]).lower() == entity_id and e["domain"] == entity_domain), None)
        
        if current_entity:
            for key, value in current_entity.items():
                if key != "domain":
                    if key.endswith("_topic"):
                        config[key] = mqtt_optolink_base_topic + value
                        config[key] = mqtt_optolink_base_topic + value
                    else:
                        config[key] = value

        # Publish MQTT message
        topic = f"{mqtt_ha_discovery_prefix}/{entity_domain}/{mqtt_ha_node_id}{entity_id}/config"
        mqtt_client.publish(topic, json.dumps(config), retain=True)

        # Short delay to allow Home Assistant to process each discovery message
        time.sleep(0.5)

        # Compact progress output
        print(f"\r[{count}/{total_entities}]", end="", flush=True)

        # Commented-out debugging details
        #print(f"\nPublished entity: {entity_name} ({entity_id})")
        #print(f"   Topic: {topic}")
        #print(f"   Payload: {json.dumps(config)}\n")


if __name__ == "__main__":
    print("\nStarting Home Assistant Entity Creation...\n")
    publish_homeassistant_entities()
    print("\n\nFinished Home Assistant Entity Creation.\n")
