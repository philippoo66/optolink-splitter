# optolink-switch/splitter
**use at your own risk!**

Announcements: 
 - There is a [branch supporting VS1 / KW protocol](https://github.com/philippoo66/optolink-splitter/blob/vs1test/)! Choose in case... ;-)
 - There are other feature branches - look at if you like

### System Overview:
![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)

Splitter for Viessmann Optolink connection [Einführungsvideo](https://youtu.be/95WIPFBxMsc)

## usage:
  1. clone files on your Pi (or other Linux or Win computer)
  2. **adjust settings in settings_ini.py** (for datapoint info see [here](https://github.com/philippoo66/ViessData21?tab=readme-ov-file#dp_listen_2zip) )
  3. run Python script optolinkvs2_switch.py (better [run it as a service](https://github.com/philippoo66/optolink-splitter/wiki/optolinkvs2_switch-automatisch-starten))
  4. feel confortable :-)

**important** for use with Vitoconnect:

regard power-on sequence at start-up:
  1. connect all the wires and plugs
  2. power on Raspi
  3. run script, wait for prompt "awaiting VS2..."
  4. power on Vitoconnect

At least with the Opto2 Vitoconnect the startup sequence is not important. This device always reconnects without problems.

When using the Vitoconnect you need to make sure that the on-board serial port is enabled and the serial console is disabled. See Wiki for [guidance](https://github.com/philippoo66/optolink-splitter/wiki/050-Prepare:-enable-serial-port,-disable-serial-console).

Attention: When connecting the CP2102 interface, make sure to **cross RX and TX lines**! What Raspi transmits (TX) the CP2102 has to receive (RX) and vice versa. Set the voltage jumper on the CP2102 TTL board to **3.3V!**

With Raspi 3 or higher you better utilize ttyAMA0 instead of ttyS0. See [here](https://github.com/philippoo66/optolink-splitter/wiki/520-termios.error:-(22,-'Invalid-argument')) for background.


## sw requirements
  - Python (not too outdated)
  - pySerial (`pip install pyserial`)
  - if MQTT is used: phao mqtt (`pip install paho-mqtt`)

  on more recent systems the use of virtual environment gets more or less 'mandatory' ("externally managed system"...). See Wiki ([here](https://github.com/philippoo66/optolink-splitter/wiki/510-error:-externally%E2%80%90managed%E2%80%90environment-%E2%80%90%E2%80%90-venv)) for details.  

## hardware requirements
  - Raspi or other computer
  - Viessmann Optolink generation device (Vitodens, Vitocal, Vitocrossal, ...)
  - Optolink r/w head (original from Viessmann, one of all the self-mades, probably a r/w head for volkszähler may work, too, if distance of LEDs gets adjusted ([8€](https://www.ebay.de/itm/285350331996)))
  - if Vitoconnect gets included: USB connection to Vitoconnect utilizing a **CP2102 chip(!)** [(e.g. this)](https://www.google.com/search?q=cp2102+usb+ttl)

**ATTENTION!** Raspi UART voltage is **3.3V** so **set the jumper on the CP2102 TTL board accordingly**!  

## command syntax MQTT, TCP/IP requests
details see [here](https://github.com/philippoo66/optolink-splitter/wiki/Command-Syntax) 

  - read ambient temperature, scaled with sign:
    - cmnd = read;0x0800;2;0.1;true
    - resp = 1;2048;8.2

  - read DeviceIdent as raw:
    - cmnd = read;0xf8;8
    - resp = 1;248;20CB1FC900000114

  - write hotwater temperature setpoint:
    - cmnd = write;0x6300;1;45
    - resp = 1;25344;45

(be careful, in case of failure don't panic, see here ([pg 2, relatively far down](https://community.viessmann.de/t5/Gas/bitte-Hilfe-Heizung-in-Fehler-Aktorentest-B3HB-Umschaltventil/m-p/439827#M113385)))

more regarding syntax see here: https://github.com/philippoo66/optolink-splitter/wiki#syntax

**important**

When using PuTTY or some like that, the session must be closed by sending `exit` (as string), because PuTTY seems not to send the FIN-Flag on getting closed.

## questions, issues

discussion, contact -> [dicussions](https://github.com/philippoo66/optolink-splitter/discussions)

issues and bug reports -> [issues](https://github.com/philippoo66/optolink-splitter/issues)

## version key
```
Vers. 1.0.0.0
      | | | |- minor revision:
      | | |    enhancements, twaeks, mods, bug fixes, no compatibility issues
      | | |- major revision:
      | |    structure/content changes, e.g. settings_ini not compatible or module added etc. or functionality added
      | |- minor version:
      |    major functionality added
      |- major version:
         program liftet to a new level
```

## more pictures
  
![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/82618777-af8b-492d-8669-e755a1172d80)



## old stuff
serlog.py is only a logging bridge to see what's going on between Vitconnect and the Optolink device.

serlog.py usage (gleiche Reihenfolge bei optolinkvs2_swich): 
1.    serielle Anschlüsse herstellen (* siehe unten)
2.    serlog.py starten (bzw. optolinkvs2_swich)
3.    Vitoconnect mit Spannung versorgen
4.    mir den Log schicken ;-) (vorher natürlich ein Weilchen laufen lassen und auch ViCare benutzen)

beim Herstellen der seriellen Verbindungen beachten:
- beim Vitoconnect vorher die Spannungsversorgung trennen (damit es erst anfängt wenn wir schon lauschen)
- beim USB2TTL
  a) auf 3.3V jumpern (Raspi UART arbeitet mit 3.3V) 
  b) +Vcc nicht verbinden (Raspi hat sein eigenes Netzteil) 
  c) Tx/Rx zwischen Raspi und USB2TTL natürlich kreuzen
