# Optolink Switch/Splitter
Make your Viessmann heating locally available via MQTT and TCP/IP while keeping Optolink/ViCare App & more!

 
#### Disclaimer
_This software is **not affiliated with, endorsed by, or associated with Viessmann** in any way. The terms Vitoconnect, Optolink, Vitocal, ViCare, etc. refer to Viessmann products and technologies. All product and brand names mentioned belong to their respective owners._ <br>
_**Use this software at your own risk.**_

## :white_check_mark: Key Benefits 
- **Local Control and Cloud Capability** – Allow full local  control and datapoint access while retaining the ability of Viessmann Cloud and App access.
- **Viessmann Heating/Heat Pump Compatibility** – Works with Vitodens, Vitocal, Vitocrossal and most other Optolink featured devices.
- **Smart Home Ready** – Integrates with **Home Assistant**, **ioBroker**, **Node-RED** or any other system with MQTT Support.


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
- [Smart Home Integration (e.g. Home Assistant)](#house-smart-home-integration-eg-home-assistant)
- [Questions & Issues](#interrobang-questions--issues)
- [3D-Printable Case for Raspberry Pi & USB-TTL Adapter](#printer-3d-printable-case-for-raspberry-pi--usb-ttl-adapter)
- [Additional Images](#camera_flash-additional-images-mqtt-visualization)


## :package: System Architecture
### How it Works
- Enables both **local monitoring/control** and **Viessmann's cloud services** in parallel.
- Data accessible via **MQTT** or TCP/IP for smart home integration (e.g. Home Assistant).
- Supports **VS2 and VS1/KW protocols** with different branches.  
  - The [vs1test branch](https://github.com/philippoo66/optolink-splitter/tree/vs1test) enables **VS1/KW protocol support** but works **only without** Vitoconnect.  
  - For **VS1/KW with Vitoconnect**, the [viconn-listener](https://github.com/philippoo66/viconn-listener) is available (currently in beta).  


### Overview
![System Architecture](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)

### Videos
🎥 **Introduction Video (German):** [Watch on YouTube](https://youtu.be/95WIPFBxMsc)

📖 **Extended Setup Tutorial (German):** [Rustimation Blog](https://www.rustimation.eu/index.php/category/iot/viessmann-ohne-api/)

## :file_folder: Software Requirements
- Python (version >= 3.9):
  - pyserial: `pip install pyserial`
  - MQTT (version >= 2.0): `pip install paho-mqtt` 
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
python3 -m venv myvenv
python3 source myvenv/bin/activate  # On Windows use: myvenv\Scripts\activate
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
python3 source myvenv/bin/activate  # Make sure to activate the virtual environment. On Windows use: venv\Scripts\activate
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

**Important Note for TCP/IP Connections:**  
When using PuTTY or similar software for a TCP/IP connection, the session must be closed by sending `exit` as a string, as PuTTY does not appear to send the FIN flag to properly terminate the session when closing.

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

