# optolink-splitter
**ACHTUNG! ABSOLUTER EXPERIMENTAL STATUS!!**

![grafik](https://github.com/philippoo66/optolink-splitter/assets/122479122/10185cc5-0eed-4bc3-a8d7-b385c4e73aaf)
<<<<<<< HEAD

Splitter for Viessmann Optolink connection planned

experimental development status!! Vitoconnect not implemented as yet!!
=======

Splitter for Viessmann Optolink connection
>>>>>>> develop

Vor dem Start von optolinkvs2_swich.py die settings_ini angucken und ggf anpassen!!


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
