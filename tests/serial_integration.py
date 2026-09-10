"""Linux pseudo-terminal integration: actual pyserial, no physical device ports."""
import os
import threading
import time
import tty
import serial
from test_parser import ParserTests, frame

case = ParserTests()
case.setUp()
case.parser.time = time
master, slave = os.openpty()
tty.setraw(slave)
port = serial.Serial(os.ttyname(slave), baudrate=4800, timeout=0)
listener = None
worker = None
try:
    packets = [frame(0x930a), frame(0x930b), frame(0x930c)]
    os.write(master, b''.join(packets))
    for index, packet in enumerate(packets):
        result = case.receive(port)
        assert result == (1, 0x930a + index, bytearray(packet)), result
    print('PASS actual pyserial: coalesced frames remain separate', flush=True)
    packet = frame()
    writer_errors = []
    def writer():
        try:
            time.sleep(2.90)
            os.write(master, packet[:4])
            time.sleep(0.20)
            os.write(master, packet[4:])
        except Exception as exc: writer_errors.append(repr(exc))
    worker = threading.Thread(target=writer, daemon=True)
    start = time.monotonic()
    worker.start()
    result = case.receive(port)
    worker.join(timeout=2)
    assert not worker.is_alive() and not writer_errors, writer_errors
    assert result == (1, 0x930a, bytearray(packet)), result
    print('PASS actual pyserial: fragmented frame crosses original idle deadline', round(time.monotonic() - start, 3), flush=True)
    # Exercise the real listener and consumer on different threads with queued frames.
    listener, _ = case.listener()
    listener.time = time
    listener_errors = []
    original_receive = listener.vs12_adapter.receive_telegr
    received = []
    all_published = threading.Event()
    def count_receive(*args, **kwargs):
        result = original_receive(*args, **kwargs)
        received.append(result)
        if len(received) == 3: all_published.set()
        return result
    listener.vs12_adapter.receive_telegr = count_receive
    def listen():
        try: listener.listen_to_Vitoconnect(port)
        except Exception as exc: listener_errors.append(repr(exc))
    worker = threading.Thread(target=listen, daemon=True)
    worker.start()
    os.write(master, b''.join(packets))
    time.sleep(0.10)
    assert len(received) == 1, received  # Unconsumed request was not overwritten.
    delivered = []
    until = time.monotonic() + 2
    while len(delivered) < 2 and time.monotonic() < until:
        value = listener.get_vicon_request()
        if value: delivered.append(value)
        time.sleep(0.01)
    assert all_published.wait(timeout=1)
    time.sleep(0.02)
    listener.exit_flag = True
    worker.join(timeout=1)
    delivered.append(listener.get_vicon_request())
    assert not worker.is_alive() and not listener_errors, listener_errors
    assert delivered == packets, delivered
    print('PASS actual pyserial: threaded listener preserves three queued requests', flush=True)
finally:
    if listener is not None:
        listener.exit_flag = True
    port.close()
    if worker is not None:
        worker.join(timeout=4)
    os.close(master)
    os.close(slave)
