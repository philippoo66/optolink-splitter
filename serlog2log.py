def convert_file(input_file, output_file):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()

    output_lines = []
    current_group = []
    last_count = None
    ts = 0
    last_ts = 0

    print(f"convering file {input_file} ...")

    for line in lines:    
        # Entfernen von fuehrenden und nachfolgenden Leerzeichen und Zeilenumbruechen
        line = line.strip()
        
        # Wenn die Zeile leer ist, ueberspringen
        if not line:
            continue

        # Zaehlen der Tabs in der Zeile
        parts = line.split('\t')
        parts_count = len(parts)

        # Wenn die Anzahl der Tabs sich aendert, schreibe die vorherige Gruppe
        if last_count and (parts_count != last_count):
            dura = int(ts) - int(last_ts)     
            output_lines.append(f"{last_count-1}\t{ts}\t{dura}\t" + " ".join(current_group))
            current_group = []
            last_ts = ts
        
        # timstamp
        if(parts_count > 1):
            ts = parts[0]               
        else:
            ts = last_ts        
        if(not last_count):
            last_ts = ts

        # Fuege die aktuelle Zeile zur Gruppe hinzu
        current_group.append(f"{parts[-1]}")
        last_count = parts_count

    # letzte
    dura = int(ts) - int(last_ts)     
    output_lines.append(f"{parts_count-1}\t{ts}\t{dura}\t" + " ".join(current_group))


    # Schreibe die Ausgabe in die output.txt Datei
    with open(output_file, 'w') as outfile:
        for output_line in output_lines:
            outfile.write(output_line + '\n')

    print(f"output written to {output_file}")


if __name__ == "__main__":
    import sys
    import os
    infile = "serlog.txt"
    if(len(sys.argv) > 1):
        infile = sys.argv[1]
    if(not os.path.exists(infile)):
        print(f"{infile} not found.\nUsage: python serlog2log.py serlog_12345678.txt")
        sys.exit()
    outfile = infile + ".csv"
    convert_file(infile, outfile)