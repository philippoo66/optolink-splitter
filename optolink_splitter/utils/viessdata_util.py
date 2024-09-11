'''
   Copyright 2024 philippoo66
   
   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import datetime
import os

import settings_ini
import utils


def get_headline() -> str:
    now = datetime.datetime.now()
    dt =  "{2:04d}-{1:02d}-{0:02d}".format(now.day, now.month, now.year)
    cols = []
    for itm in settings_ini.poll_items:
        cols.append(itm[1])
    capts = ';'.join([format(addr, '04X') for addr in cols])
    return f";{dt};{capts};"


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
    return int((now - monday_midnight).total_seconds() // 60)

def formatted_timestamp() -> str:
    # Aktuellen Zeitstempel abrufen
    now = datetime.datetime.now()
    # Wochentag abrufen und in das entsprechende Kürzel umwandeln
    weekday = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][now.weekday()]
    # Zeitstempel im gewünschten Format erstellen
    return "{0}-{1:02d}:{2:02d}:{3:02d}".format(weekday, now.hour, now.minute, now.second)


wrbuffer = []
mins_old = 0
recent_filename = get_filename()

def buffer_csv_line(data, force_write=False):
    global wrbuffer
    global mins_old
    global recent_filename

    sline = None

    mins_new = minutes_since_monday_midnight()
    new_week = (mins_new < mins_old)  # new week
    mins_old = mins_new

    buffer_full = (len(wrbuffer) >= settings_ini.buffer_to_write)

    if(data):
        sline = str(mins_new) + ";"
        sline += formatted_timestamp() + ";"

        # decimal separator
        if(settings_ini.dec_separator == ","):
            tbreplaced = "."
        else:
            tbreplaced = ","
        for i in range(0, len(settings_ini.poll_items)):
            sval = str(data[i])
            if(utils.to_number(data[i]) != None):
                # format number, anything else left like it is
                sval = sval.replace(tbreplaced, settings_ini.dec_separator) 
            sline += sval + ";"

        if(force_write and not new_week):
            wrbuffer.append(sline)
            sline = None


    if(force_write or new_week or buffer_full):
        csvfile = os.path.join(settings_ini.viessdata_csv_path, recent_filename)
        writehd = (not os.path.exists(csvfile))
        with open(csvfile, 'a') as f:
            if(writehd):
                hl = get_headline()
                f.write(hl + '\n')
            for ln in wrbuffer:
                f.write(ln + '\n')
            f.flush()
        wrbuffer = []
        recent_filename = get_filename()

    if(sline is not None):
        wrbuffer.append(sline)


# main for test only
if __name__ == "__main__":
    print(get_headline())
    print(get_filename())
    # Minuten seit Montag 0 Uhr 0 Minuten berechnen und ausgeben
    print("Minuten seit Montag 0 Uhr 0 Minuten:", minutes_since_monday_midnight())
    # Formatierter Zeitstempel ausgeben
    print("Formatierter Zeitstempel:", formatted_timestamp())
    # Formatierter Zeitstempel ausgeben
#    print("Formatierter Zeitstempel2:", formatted_timestamp2())
