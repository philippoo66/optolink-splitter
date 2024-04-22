import datetime
import os

import settings_ini


def get_headline() -> str:
    now = datetime.datetime.now()
    dt =  "{2:04d}-{1:02d}-{0:02d}".format(now.day, now.month, now.year)
    cols = []
    for itm in settings_ini.poll_items:
        cols.append(itm[1])
    capts = ';'.join([format(addr, '04X') for addr in cols])
    return ";" + dt + ";088E;" + capts + ";"


def get_filename() -> str:
    now = datetime.datetime.now()
    yr, cw, _ = now.isocalendar()
    return "{0:04d}_KW{1:02d}_data.csv".format(yr, cw)


def minutes_since_monday_midnight() -> int:
    # Aktuelles Datum und Uhrzeit abrufen
    now = datetime.datetime.now()
    
    # Montag 0 Uhr 0 Minuten berechnen
    monday_midnight = now - datetime.timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    
    # Differenz zwischen dem aktuellen Zeitpunkt und Montag 0 Uhr 0 Minuten in Minuten berechnen
    minutes_since_monday_midnight = int((now - monday_midnight).total_seconds() // 60)
    
    return minutes_since_monday_midnight


def formatted_timestamp() -> str:
    # Aktuellen Zeitstempel abrufen
    now = datetime.datetime.now()
    
    # Wochentag abrufen und in das entsprechende Kürzel umwandeln
    weekday = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][now.weekday()]
    
    # Zeitstempel im gewünschten Format erstellen
    timestamp = "{0}-{1:02d}:{2:02d}:{3:02d}".format(weekday, now.hour, now.minute, now.second)
    
    return timestamp


def formatted_timestamp2() -> str:
    # Aktuellen Zeitstempel abrufen
    now = datetime.datetime.now()
    
    # Wochentag abrufen und in das entsprechende Kürzel umwandeln
    weekday = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][now.weekday()]
    
    # Datum im gewünschten Format erstellen (z.B. "08.04.2024")
    date = "{0:02d}.{1:02d}.{2}".format(now.day, now.month, now.year)
    
    # Zeitstempel im gewünschten Format erstellen
    timestamp = "{0} {1} {2:02d}:{3:02d}:{4:02d}".format(weekday, date, now.hour, now.minute, now.second)
    
    return timestamp


def write_csv_line(data):
    csvfile = get_filename()
    csvfile = os.path.join(settings_ini.viessdata_csv_path, csvfile)
    writehd = (not os.path.exists(csvfile))
    sline = str(minutes_since_monday_midnight()) + ";"
    sline += formatted_timestamp() + ";"
    sline += formatted_timestamp2() + ";"

    if(settings_ini.dec_separator == ","):
        tbreplaced = "."
    else:
        tbreplaced = ","
     
    for i in range(0, len(settings_ini.poll_items)):
        sval = str(data[i])
        if not isinstance(settings_ini.poll_items[i][3], str):
            # fomat number, anything else left like it is
            sval = sval.replace(tbreplaced, settings_ini.dec_separator) 
        sline += sval + ";"

    with open(csvfile, 'a') as f:
        if(writehd):
            hl = get_headline()
            f.write(hl + '\n')
        f.write(sline + '\n')


if __name__ == "__main__":
    print(get_headline())
    print(get_filename())
    # Minuten seit Montag 0 Uhr 0 Minuten berechnen und ausgeben
    print("Minuten seit Montag 0 Uhr 0 Minuten:", minutes_since_monday_midnight())
    # Formatierter Zeitstempel ausgeben
    print("Formatierter Zeitstempel:", formatted_timestamp())
    # Formatierter Zeitstempel ausgeben
    print("Formatierter Zeitstempel2:", formatted_timestamp2())