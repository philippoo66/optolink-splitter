# Optolink Switch/Splitter
Make your Viessmann heating locally available via MQTT while keeping Optolink/ViCare App & more!

 
#### Disclaimer
_This software is **not affiliated with, endorsed by, or associated with Viessmann** in any way. The terms Vitoconnect, Optolink, Vitocal and ViCare refer to Viessmann products and technologies. All product and brand names mentioned belong to their respective owners. 
**Use this software at your own risk.**_

## :white_check_mark: Key Benefits 
- **Cloud & Local Control** – Retain Viessmann Cloud and App access while enabling full local  control and datapoint access.
- **Viessmann Heating/Heat Pump Compatibility** – Works with Vitodens, Vitocal, Vitocrossal, and other Optolink featured devices.  
- **Smart Home Ready** – Integrates with **ioBroker**, **Home Assistant**, **Node-RED** or any other system with MQTT Support.


## 🎉 Announcements
- **Version 1.2.0.0 is out!** Check the [changelog](https://github.com/philippoo66/optolink-splitter/wiki/990-Version-Log#version-1200) for details.
- Need **VS1 / KW protocol support**? Use the [dedicated branch](https://github.com/philippoo66/optolink-splitter/blob/vs1test/).
- Explore other feature branches, there might be something useful for you! 😉


## 📌 Table of Contents
- [System Architecture](#package-system-architecture)
- [Software Requirements](#file_folder-software-requirements)
- [Hardware Requirements](#desktop_computerhardware-requirements)
- [Installation](#hammer_and_wrench-installation)
- [Getting Started](#rocket-getting-started)
- [Command Syntax: MQTT & TCP/IP](#receipt-command-syntax-mqtt--tcpip)
- [Questions & Issues](#interrobang-questions--issues)
- [Version Key](#1234-version-key)
- [Printable Case](#printable-raspberry-pi-case--usb-ttl-case)
- [Additional Images](#camera_flash-additional-images-mqtt-home-assistant)


## :package: System Architecture
### How it Works
- Enables both **Viessmann's cloud services** and **local monitoring/control** in parallel.
- Data accessible via **MQTT** for smart home integration (e.g. Home Assistant).
- Supports **VS2 and VS1/KW protocols** with different branches.
  - branch [vs1test](https://github.com/philippoo66/optolink-splitter/tree/vs1test) works as with VS1/KW protocol but only _without_ Vitoconnect.
  - for VS1/KW _with_ Vitoconnect there is the [viconn-listener](https://github.com/philippoo66/viconn-listener) available (beta state).


### Overview
![System Architecture](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)

### Videos
🎥 **Introduction Video (German):** [Watch on YouTube](https://youtu.be/95WIPFBxMsc)

📖 **Extended Setup Tutorial (German):** [Rustimation Blog](https://www.rustimation.eu/index.php/category/iot/viessmann-ohne-api/)

## :file_folder: Software Requirements
- Python >= 3.9:
  - pyserial: `pip install pyserial`
  - MQTT: `pip install paho-mqtt` version >= 2.0
- Virtual environments recommended ([Guide](https://github.com/philippoo66/optolink-splitter/wiki/510-error:-externally%E2%80%90managed%E2%80%90environment-%E2%80%90%E2%80%90-venv)).

## :desktop_computer:	Hardware Requirements
- Raspberry Pi or a suitable system.
- Viessmann Optolink-compatible heating (Vitodens, Vitocal, Vitocrossal, etc.).
- Optolink r/w head:
  - Original Viessmann model or self-made.
  - Volkszähler-compatible versions may work if LED distance is adjusted ([8€ option](https://www.ebay.de/itm/285350331996)).
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
python3 -m venv venv
python3 source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

#### 2.2. Install required dependencies:
```sh
pip install pyserial
pip install paho-mqtt  # Only if MQTT is used
```
*NOTE:* After installation, the environment must be activated each time before running the script.

### 3. Configure the Settings
Modify `settings_ini.py` according to your heating (/ datapoints):
- Refer to [Wiki | Parameter Addresses](https://github.com/philippoo66/optolink-splitter/wiki/310-Parameter-Addresses)
- Refer to [Wiki | ViessData21](https://github.com/philippoo66/ViessData21?tab=readme-ov-file#dp_listen_2zip)

### 5. Run the Script
```sh
python3 source venv/bin/activate  # Make sure to activate the virtual environment. On Windows use: venv\Scripts\activate
python3 optolinkvs2_switch.py
```
For automatic startup, set up a service. See the [Wiki Guide](https://github.com/philippoo66/optolink-splitter/wiki/120-optolinkvs2_switch-automatisch-starten).

## :rocket: Getting Started
### Parallel use with Vitoconnect / ViCare App
- Ensure the **serial port is enabled** and **serial console is disabled** ([Guide](https://github.com/philippoo66/optolink-splitter/wiki/050-Prepare:-enable-serial-port,-disable-serial-console)).
- **CP2102 Interface:**
  - Cross **RX/TX** lines.
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
For more details on the command syntax, see the [Wiki | Command Syntax Overview](https://github.com/philippoo66/optolink-splitter/wiki/010-Command-Syntax) or go directly to the section on [MQTT and TCP/IP requests](https://github.com/philippoo66/optolink-splitter/wiki/010-Command-Syntax#command-syntax-for-requests-via-mqtt-and-tcpip).


### Read Ambient Temperature (scaled with sign)
```sh
cmnd = read;0x0800;2;0.1;true
```

```sh
resp = 1;2048;8.2
```

### Read DeviceIdent (raw)
```sh
cmnd = read;0xf8;8

```

```sh
resp = 1;248;20CB1FC900000114
```

### Set Hot Water Temperature Setpoint
```sh
cmnd = write;0x6300;1;45
```

```sh
resp = 1;25344;45
```

## :1234: Version Key
```
Vers. 1.0.0.0
      | | | |- minor revision: Enhancements, tweaks, bug fixes.
      | | |- major revision: Structure/content changes, new modules.
      | |- minor version: Major functionality added.
      |- major version: Program lifted to a new level.
```

## :interrobang: Questions & Issues
- Discussions & contact: [GitHub Discussions](https://github.com/philippoo66/optolink-splitter/discussions)
- Bug reports: [GitHub Issues](https://github.com/philippoo66/optolink-splitter/issues)

## Printable Raspberry Pi Case / USB-TTL Case 
[Raspberry Pi 3 case with CP board holder](https://www.printables.com/model/1144565-raspberry-pi-3-b-sleeve-case-w-cp2102-holder-wall) (Possibly for Pi 4 in future). Thanks to [Kristian](https://github.com/kristian)!

## :camera_flash: Additional Images (MQTT, Home Assistant)
### Datapoints in settings_ini.py & MQTT Explorer monitoring
![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/82618777-af8b-492d-8669-e755a1172d80)
 
### Data visualisation
![grafik](https://github.com/user-attachments/assets/fee2151f-7d99-45a0-a85a-897b54085289)

### Heating System Overview implemented in Home Assistant
![grafik](https://github.com/user-attachments/assets/28901428-5cec-4135-aada-795302d58811)

ref. https://github.com/philippoo66/optolink-splitter/discussions/67


