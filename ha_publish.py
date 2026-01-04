import json
import paho.mqtt.client as paho
import time

from c_settings_adapter import settings

from ha_shared_config import shared_config

# Global MQTT Client
mqtt_client = None

def connect_mqtt(retries=3, delay=5):
    """Global MQTT Client für dieses Script."""
    global mqtt_client
    
    if mqtt_client is None:
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2, "datapoints_" + str(int(time.time()*1000)))
    
    if mqtt_client.is_connected():
        print(" MQTT client is already connected. Skipping reconnection.")
        return True
    
    try:
        mqtt_credentials = settings.mqtt.split(':')
        MQTT_BROKER, MQTT_PORT = mqtt_credentials[0], int(mqtt_credentials[1])
        
        mqtt_user_pass = settings.mqtt_user
        if mqtt_user_pass and mqtt_user_pass.lower() != "none":
            mqtt_user, mqtt_password = mqtt_user_pass.split(":")
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
            print(f"Connecting as {mqtt_user} to MQTT broker {MQTT_BROKER}:{MQTT_PORT}...")
        else:
            print(f"Connecting anonymously to MQTT broker {MQTT_BROKER}:{MQTT_PORT}...")
        
        for attempt in range(retries):
            try:
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                mqtt_client.loop_start()
                print(" ✓ MQTT connected successfully.")
                return True
            except Exception as retry_error:
                print(f" ERROR: MQTT connection failed (Attempt {attempt+1}/{retries}): {retry_error}")
                time.sleep(delay)
        
        print(" ERROR: Could not establish MQTT connection after multiple retries.")
        return False
        
    except Exception as e:
        print(f" ERROR connecting to MQTT broker: {e}")
        return False

def verify_mqtt_optolink_lwt(timeout=10):
    """Verifies Optolink-Splitter availability via LWT."""
    global mqtt_client
    
    if mqtt_client is None:
        print(" ERROR: MQTT client is not initialized.")
        return False
    
    LWT_TOPIC = settings.mqtt_topic + "/LWT" 
    lwt_status = {"online": False}
    
    def on_message(client, userdata, message):
        payload = message.payload.decode()
        if payload == "online":
            print(f" ✓ Optolink-Splitter LWT reports 'online'.")
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
    print(" Ensure optolinkvs2_switch.py is running.")
    return False

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
    # MQTT verbinden und prüfen
    if not connect_mqtt():
        print(" ERROR: MQTT connection failed. Exiting.")
        return
    if not verify_mqtt_optolink_lwt():
        print(" ERROR: Optolink-Splitter offline. Exiting.")
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
            mqtt_client.publish(topic, json.dumps(discovery_config), retain=True)
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
