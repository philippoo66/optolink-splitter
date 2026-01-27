# Optolink Switch/Splitter
Make your Viessmann heating locally available via MQTT and TCP/IP while keeping Optolink/ViCare App & more!

![System Architecture](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)

**Use this software at your own risk.**

For latest developments always check the [Version-Log](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log)

## 🎉 Announcements
- [**Version 1.10.0.0**](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log#version-11000) **New Feature: User-Friendly MQTT /set Topics!** Write values using the same format they're published in! Example: Publish `vito/c1_temp_room_setpoint/set` with payload `21.5` instead of complex command syntax. Supports ON/OFF, boolean, and numeric values with automatic scaling. See [MQTT_SET_TOPICS.md](MQTT_SET_TOPICS.md) for details.

- [**Version 1.9.0.2**](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log#version-1902) **Home Assistant integration** simplified! Define Entities and poll_list together in `ha_shared_config.py` and run `ha_publish.py` once and everything is fine! Thank you @matthias-oe, @EarlSneedSinclair!

- [**Version 1.8.3.0**](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log#version-1601) Adds MQTT TLS support (optional). TLS/SSL mode for the MQTT client possible. Thank you @EarlSneedSinclair!

- Need **VS1 / KW protocol support**? It got implemented in the main tree since V1.8.0.0. Just set `vs1protocol = True`<br>
Still **TESTERS WANTED with KW device and Vitoconnnect!**

- minimal Optolink Adapter confirmed:

![grafik](https://github.com/user-attachments/assets/e2566c68-b461-403b-918e-fa5774c71b5d)



## 📌 Table of Contents
- [Introduction](#rocket-introduction)
- [Software Requirements](#file_folder-software-requirements)
- [Hardware Requirements](#desktop_computerhardware-requirements)
- [Installation](#hammer_and_wrench-installation)
- [Updating to a new Version](#updating-to-a-new-version)
- [Connecting Optolink & Vitoconnect](#electric_plug-connecting-optolink--vitoconnect)
- [Command Syntax: MQTT & TCP/IP](#receipt-command-syntax-mqtt--tcpip)
- [User-Friendly MQTT /set Topics](#pushpin-user-friendly-mqtt-set-topics)
- [Smart Home Integration (e.g. Home Assistant)](#house-smart-home-integration-eg-home-assistant)
- [Questions & Issues](#interrobang-questions--issues)
- [3D-Printable Case for Raspberry Pi & USB-TTL Adapter](#printer-3d-printable-case-for-raspberry-pi--usb-ttl-adapter)
- [Additional Images](#camera_flash-additional-images-mqtt-visualization)
- [Disclaimer](#memo-disclaimer)


## :rocket: Introduction

### Key Benefits 
- **Local Control and Cloud Capability** – Allow full local  control and datapoint access while retaining the ability of Viessmann Cloud and App access.
- **Viessmann Heating/Heat Pump Compatibility** – Works with Vitodens, Vitocal, Vitocrossal and most other Optolink featured devices.
- **Smart Home Ready** – Integrates with **Home Assistant**, **ioBroker**, **Node-RED** or any other system with MQTT Support.
- Supports **VS2/300 and VS1/KW protocols** now within a single branch.  
  - with VS1/KW devices/protocol probably Vitoconnect might not work. **TESTER WANTED with KW device and Vitoconnect!**  
  - For **VS1/KW with Vitoconnect**, the [viconn-listener](https://github.com/philippoo66/viconn-listener) is available (currently in beta).

### Videos
🎥 **Introduction Video (German):** [Watch on YouTube](https://youtu.be/95WIPFBxMsc)

📖 **Extended Setup Tutorial (German):** [Rustimation Blog](https://www.rustimation.eu/index.php/category/iot/viessmann-ohne-api/)

## :file_folder: Software Requirements
- Python (version >= 3.9):
  - pyserial: `pip install pyserial`
  - MQTT (version >= 2.0): `pip install paho-mqtt` 
- Virtual environment recommended ([Guide](https://github.com/philippoo66/optolink-splitter/wiki/510-error:-externally%E2%80%90managed%E2%80%90environment-%E2%80%90%E2%80%90-venv)).

## :desktop_computer:	Hardware Requirements
- Raspberry Pi or a suitable system.
- Viessmann Optolink-compatible heating (Vitodens, Vitocal, Vitocrossal, etc.).
- Optolink r/w head:
  - Original Viessmann model or self-made.
  - Volkszaehler-compatible versions may work if LED distance is adjusted ([8€ option](https://www.ebay.de/itm/285350331996)).
- To retain **ViCare App functionality**, use a USB-to-TTL adapter:
  - Recommended: CP2102 chip ([Example](https://www.google.com/search?q=cp2102+usb+ttl)).
  - Some newer Vitoconnect models may work with FTDI chips.
  - **Raspberry Pi UART voltage = 3.3V** → Set jumper accordingly!

## :hammer_and_wrench: Installation
### 1. Clone the Repository
```sh
git clone https://github.com/philippoo66/optolink-splitter.git
cd optolink-splitter
```

### 2. Create Virtual Environment & Install Dependencies

Using a virtual environment is recommended to keep dependencies isolated and avoid conflicts with system-wide packages. More details can be found in [this guide](https://github.com/philippoo66/optolink-splitter/wiki/510-error:-externally%E2%80%90managed%E2%80%90environment-%E2%80%90%E2%80%90-venv).

#### 2.1. Create & activate the virtual environment:
```sh
python3 -m venv myvenv
source myvenv/bin/activate  # On Windows use: myvenv\Scripts\activate
```

#### 2.2. Install required dependencies:
```sh
pip install pyserial
pip install paho-mqtt  # Only if MQTT is used
```
*NOTE:* After installation, the environment must be activated before running the script.

### 3. Configure the Settings
Modify `settings_ini.py` according to your heating (/ datapoints):
- Refer to [Wiki | Parameter Addresses](https://github.com/philippoo66/optolink-splitter/wiki/310-Parameter-Addresses), [poll_list samples](https://github.com/philippoo66/optolink-splitter/wiki/350-Poll-Configuration-Samples)
- Refer to [Wiki | ViessData21](https://github.com/philippoo66/ViessData21?tab=readme-ov-file#dp_listen_2zip)

### 4. Run the Script
```sh
source myvenv/bin/activate  # Make sure to activate the virtual environment. On Windows use: venv\Scripts\activate
python3 optolinkvs2_switch.py
```
For automatic startup, set up a service. See the [Wiki Guide](https://github.com/philippoo66/optolink-splitter/wiki/120-optolinkvs2_switch-automatisch-starten).

## Updating to a new Version
If you want to update your installation to a new version, the recommended way is to
- make a backup copy of your current installation (folder)
- from the new version repo, clone **all files except settings_ini.py** into your original folder (replace existing files)
- check the [version log](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log) for added or changed entries in the settings_ini and apply (only) those changes to your existing settings_ini.py 

Alternatively you might clone all files and apply your original settings to the new settings_ini afterwards.

Don't forget to restart the script / the service afterwards.

Even though I promise to note required changes carefully in the version log from now on, after an update it is always a good practice to start the splitter once in the console (`python optolinkvs2_switch.py`, remember to run your virtual environment) since in the console you get quite detailed error messages _if_ some would be wrong or missing.

## :electric_plug: Connecting Optolink & Vitoconnect
### Parallel use with Vitoconnect / ViCare App
- Ensure the **serial port is enabled** and **serial console is disabled** ([Guide](https://github.com/philippoo66/optolink-splitter/wiki/050-Prepare:-enable-serial-port,-disable-serial-console)).
- **CP2102 Interface:**
  - **Cross RX/TX** lines.
  - Set voltage jumper to **3.3V**.
  - Use `ttyAMA0` instead of `ttyS0` for Raspberry Pi 3+ ([Details](https://github.com/philippoo66/optolink-splitter/wiki/520-termios.error:-(22,-'Invalid-argument'))).

### Vitoconnect Interfaces
#### **Vitoconnect 100 OPTO1**
To ensure proper communication with the system, follow the power-on sequence exactly:
1. **Connect all wires and plugs** to the Raspberry Pi and Vitoconnect.
2. **Power on the Raspberry Pi**.
3. Run the script and wait for the prompt: `awaiting VS2...`.
4. **Power on Vitoconnect 100 OPTO1**.

#### **Vitoconnect OPTO2**
The startup sequence for this device is not critical, as it will automatically reconnect without issues.

## :receipt: Command Syntax: MQTT & TCP/IP
Optolink Splitter can connect to an **MQTT Broker** for sending commands and receiving responses. Alternatively, a direct **TCP/IP connection** (e.g. using PuTTY) can be established to interact with the application directly. For more details on the command syntax, see the [Wiki | Command Syntax Overview](https://github.com/philippoo66/optolink-splitter/wiki/010-Command-Syntax) or go directly to the section on [MQTT and TCP/IP requests](https://github.com/philippoo66/optolink-splitter/wiki/010-Command-Syntax#command-syntax-for-requests-via-mqtt-and-tcpip).


  - read ambient temperature, scaled with sign:
    - cmnd = read;0x0800;2;0.1;true
    - resp: 1;2048;8.2

  - read DeviceIdent as raw:
    - cmnd = read;0xf8;8
    - resp: 1;248;20CB1FC900000114

  - write hotwater temperature setpoint:
    - cmnd = write;0x6300;1;45
    - resp: 1;25344;45

**Note for TCP/IP Connections:**  
You may close the TCP session by sending `exit` as a string.

## :pushpin: User-Friendly MQTT /set Topics
In addition to the command syntax above, you can now write values using simple MQTT topics.
For every datapoint published to MQTT (e.g., `vito/hk1_normal_temperature`), you can write to it using a `/set` suffix:
```bash
# Reading (automatic, via poll_list)
Topic: vito/hk1_normal_temperature
Payload: 20.5

# Writing (simple and intuitive!)
Topic: vito/hk1_normal_temperature/set
Payload: 21.0
```

**Quick Examples:**
```bash
# Set room temperature (automatic scaling applied)
mosquitto_pub -t "vito/hk1_normal_temperature/set" -m "21.5"

# State on/off
mosquitto_pub -t "vito/hk1_partymode/set" -m "ON"
mosquitto_pub -t "vito/hk1_partymode/set" -m "OFF"

# Set hot water temperature
mosquitto_pub -t "vito/hotwater_temperature/set" -m "50"
```

For complete documentation with more examples, see **[MQTT_SET_TOPICS.md](MQTT_SET_TOPICS.md)**.

## :house: Smart Home Integration (e.g. Home Assistant)
Optolink Splitter seamlessly integrates into your smart home setup via **MQTT**, allowing you to monitor and control your Viessmann heating system using platforms like **Home Assistant**, **ioBroker**, or **Node-RED**. All available heating system data can be visualized in dashboards, automated with custom rules, and integrated into broader smart home routines. With Optolink Splitter’s command-sending capability, you can locally adjust heating modes, temperature setpoints, or pump states directly from your favorite smart home system.

For detailed **Home Assistant integration instructions**, see the [Wiki | Home Assistant Integration of Optolink‐Splitter](https://github.com/philippoo66/optolink-splitter/wiki/210-Home-Assistant-Integration-of-Optolink%E2%80%90Splitter).  

Below are examples of how this integration looks in different smart home environments:

### Heating System Overview in Home Assistant (Built with a Picture Entity Card)
![grafik](https://github.com/user-attachments/assets/28901428-5cec-4135-aada-795302d58811)

[Details](https://github.com/philippoo66/optolink-splitter/discussions/67)

### Another Heating System Overview in Home Assistant & Command Buttons
![0b87f133-3285-4cb5-871c-87c66598d42d](https://github.com/user-attachments/assets/596c2f3d-24c3-406a-854b-4679ce0643d7)

## :interrobang: Questions & Issues
- Discussions & contact: [GitHub Discussions](https://github.com/philippoo66/optolink-splitter/discussions)
- Bug reports: [GitHub Issues](https://github.com/philippoo66/optolink-splitter/issues)

## :printer: 3D-Printable Case for Raspberry Pi & USB-TTL Adapter
A compact and practical 3D-printable case designed for Raspberry Pi 2 & 3 including a CP2102 USB-TTL adapter mount.  A version for **Raspberry Pi 4** may be available in the future. Special thanks to [Kristian](https://github.com/kristian)!  

[Raspberry Pi 2/3 Case with CP2102 UART Board Holder](https://www.printables.com/model/1144565-raspberry-pi-3-b-sleeve-case-w-cp2102-holder-wall)  

## :camera_flash: Additional Images (MQTT, Visualization)
### Datapoints in settings_ini.py & MQTT Explorer monitoring
![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/82618777-af8b-492d-8669-e755a1172d80)
 
### Data visualisation
![grafik](https://github.com/user-attachments/assets/fee2151f-7d99-45a0-a85a-897b54085289)

## :memo: Disclaimer
This software is **not affiliated with, endorsed by, or associated with Viessmann** in any way. The terms Vitoconnect, Optolink, Vitocal, ViCare, etc. refer to Viessmann products and technologies. All product and brand names mentioned belong to their respective owners.<br>
It is provided **as-is**, without any warranties or guarantees. The authors assume no liability for any issues arising from its use. 

