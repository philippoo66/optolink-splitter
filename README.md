# optolink-splitter
Splitter for Viessmann Optolink connection planned

experimental development status!!

serlog.py is currently only a logging bridge to see what's going on between Vitconnect and the Optolink device.

see https://github.com/philippoo66/py-optolink for communication


serlog.py usage:
1.    serielle Anschlüsse herstellen (* siehe unten)
2.    serlog.py starten
3.    Vitoconnect mit Spannung versorgen
4.    mir den Log schicken ;-) (vorher natürlich ein Weilchen laufen lassen)

beim Herstellen der seriellen Verbindungen beachten:
- beim Vitoconnect vorher die Spannungsversorgung trennen (damit es erst anfängt wenn wir schon lauschen)
- beim TTL2USB
  a) auf 3.3V jumpern (Raspi UART arbeitet mit 3.3V) und 
  b) +Vcc nicht verbinden (Raspi hat sein eigenes Netzteil)
