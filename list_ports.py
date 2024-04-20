import serial.tools.list_ports

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("Keine seriellen Ports gefunden.")
    else:
        print("Verfügbare serielle Ports:")
        for port, desc, hwid in sorted(ports):
            print(f"{port}: {desc} [{hwid}]")

if __name__ == "__main__":
    list_serial_ports()
