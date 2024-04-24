# optolink-splitter
**development status!! use at your own risk!**

![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)

Splitter for Viessmann Optolink connection

## usage:
  1. clone files on your Pi (or other Linux or Win computer)
  2. adjust settings in settings_ini.py
  3. run Python script optolinkvs2_switch.py
  4. feel confortable :-)
     
**important**
regard power-on sequence at start-up:
  1. connect all the wires and plugs
  2. power on Raspi
  3. run script, wait for prompt "awaiting VS2..."
  4. power on Vitoconnect

## sw requirements
  - Python (not too outdated)
  - if MQTT is used: phao mqtt (pip install paho-mqtt)

## hardware requirements
  - Raspi or other computer
  - Viessmann Optolink generation device (Vitodens, Vitocal, Vitocrossal, ...)
  - Optolink r/w head (original from Viessmann, one of all the self-mades, probably a r/w head for volkszähler may work, too, if distance of LEDs gets adjusted ([8€](https://www.ebay.de/itm/285350331996)))
  - if Vitoconnect gets included: USB connection to Vitoconnect utilizing a **CP2102 chip(!)** [(e.g. this)](https://www.amazon.de/dp/B0B18JKYBF)

## command syntax MQTT, TCP/IP requests
  - read ambient temperature, scaled with sign:
    - cmnd = read;0x0800;2;0.1;true
    - resp = 1;2048;8.2

  - read DeviceIdent as raw:
    - cmnd = read;0xf8;8
    - resp = 1;248;20CB1FC900000114

  - write hotwater temperature stepoint:
    - cmnd = write;0x6300;1;45
    - resp = 1;25344;45

(be careful, in case of failure don't panic, see here ([pg 2, relatively far down](https://community.viessmann.de/t5/Gas/bitte-Hilfe-Heizung-in-Fehler-Aktorentest-B3HB-Umschaltventil/m-p/439827#M113385)))

more regarding syntax see here: https://github.com/philippoo66/optolink-splitter/wiki#syntax

## questions, issues
-> [dicussions](https://github.com/philippoo66/optolink-splitter/discussions)
-> [issues](https://github.com/philippoo66/optolink-splitter/issues)

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
