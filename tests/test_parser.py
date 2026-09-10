"""Behavior regressions using complete candidate modules; no device I/O.

Run: python3 -m unittest discover -s tests -p "test_*.py" -v
"""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest

TARGET = Path(os.environ.get("OPTOLINK_TEST_ROOT", Path(__file__).resolve().parents[1]))

class Clock:
    def __init__(self): self.us = 0
    def monotonic(self): return self.us / 1_000_000
    def sleep(self, seconds): self.us += round(seconds * 1_000_000)

class Serial:
    def __init__(self, clock, chunks):
        self.clock = clock
        self.chunks = list(chunks)
        self.buffer = bytearray()
        self.writes = bytearray()
    def release(self):
        while self.chunks and self.chunks[0][0] <= self.clock.us:
            self.buffer.extend(self.chunks.pop(0)[1])
    def read(self, size=1):
        assert size > 0, size
        self.release()
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result
    def read_all(self):
        self.release()
        result = bytes(self.buffer)
        self.buffer.clear()
        return result
    def write(self, data): self.writes.extend(data); return len(data)

def load(name, filename, deps):
    spec = importlib.util.spec_from_file_location(name, TARGET / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, deps): spec.loader.exec_module(module)
    return module

def frame(address=0x930a, data=b'', response=False, error=False):
    payload = bytes([3 if error else int(response), 1, address >> 8, address & 255,
                     len(data) if response else 3]) + data
    body = bytes([len(payload)]) + payload
    result = b'\x41' + body + bytes([sum(body) & 255])
    return (b'\x06' if response else b'') + result

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.errors = []
        self.callbacks = []
        self.deps = {
            'serial': NS(Serial=Serial),
            'c_settings_adapter': NS(settings=NS(show_opto_rx=False)),
            'logger_util': NS(logger=NS(error=lambda *a:None, warning=lambda *a:None)),
            'utils': NS(comm_error=self.errors.append, bbbstr=lambda d:bytes(d).hex()),
        }
        self.parser = load('tested_parser', 'optolinkvs2.py', self.deps)
        self.parser.time = self.clock
    def receive(self, source, response=False, raw=True, sink=None):
        return self.parser.receive_telegr(response, raw, source, sink, lambda *args:self.callbacks.append(args))
    def source(self, *chunks): return Serial(self.clock, chunks)
    def test_request_arriving_near_idle_deadline_gets_full_frame_budget(self):
        request = frame()
        result = self.receive(self.source((2_995_000, request[:4]), (3_020_000, request[4:])))
        self.assertEqual(result, (1, 0x930a, bytearray(request)))
        self.assertEqual(self.errors, [False])
    def test_ack_near_idle_deadline_then_fragmented_response(self):
        reply = frame(data=b'abc', response=True)
        source = self.source((2_995_000, reply[:1]), (3_005_000, reply[1:5]), (3_030_000, reply[5:]))
        self.assertEqual(self.receive(source, True), (1, 0x930a, bytearray(reply)))
    def test_two_coalesced_requests_return_separately_in_order(self):
        first, second = frame(), frame(0x930b)
        source = self.source((0, first + second))
        self.assertEqual(self.receive(source), (1, 0x930a, bytearray(first)))
        self.assertEqual(self.receive(source), (1, 0x930b, bytearray(second)))
        self.assertFalse(source.buffer)
        self.assertEqual([c[1] for c in self.callbacks], [0x930a, 0x930b])
    def test_coalesced_responses_forward_each_byte_once(self):
        replies = [frame(a, data=bytes([a & 255]), response=True) for a in (0x930a, 0x930b, 0x930c)]
        source, sink = self.source((0, b''.join(replies))), self.source()
        for index, reply in enumerate(replies):
            self.assertEqual(self.receive(source, True, sink=sink), (1, 0x930a + index, bytearray(reply)))
            self.assertEqual(sink.writes, b''.join(replies[:index + 1]))
    def test_every_fragment_boundary_request_and_response(self):
        for response in (False, True):
            packet = frame(data=b'abc' if response else b'', response=response)
            for boundary in range(1, len(packet)):
                with self.subTest(response=response, boundary=boundary):
                    self.clock.us = 0
                    source = self.source((0, packet[:boundary]), (25_000, packet[boundary:]))
                    self.assertEqual(self.receive(source, response), (1, 0x930a, bytearray(packet)))
    def test_single_byte_fragments(self):
        packet = frame(data=b'xyz', response=True)
        source = self.source(*[(index * 5_000, bytes([value])) for index, value in enumerate(packet)])
        self.assertEqual(self.receive(source, True), (1, 0x930a, bytearray(packet)))
    def test_maximum_payload_and_following_frame(self):
        packet, following = frame(data=bytes(range(250)), response=True), frame(response=True)
        source = self.source((0, packet + following))
        self.assertEqual(self.receive(source, True)[2], packet)
        self.assertEqual(self.receive(source, True)[2], following)
    def test_decoded_payload_and_callback_stay_compatible(self):
        packet = frame(data=b'xyz', response=True)
        self.assertEqual(self.receive(self.source((0, packet)), True, False), (1, 0x930a, bytearray(b'xyz')))
        self.assertEqual(self.callbacks, [(1, 0x930a, bytearray(b'xyz'), 1, 0, 1, 3)])
    def test_idle_timeout_is_bounded(self):
        self.assertEqual(self.receive(self.source()), (255, 0, bytearray()))
        self.assertGreaterEqual(self.clock.us, 3_000_000)
        self.assertLessEqual(self.clock.us, 3_005_000)
    def test_incomplete_frame_timeout_is_bounded(self):
        result = self.receive(self.source((2_990_000, b'\x41\x05')))
        self.assertEqual(result, (255, 0, bytearray(b'\x41\x05')))
        self.assertGreaterEqual(self.clock.us, 5_990_000)
        self.assertLessEqual(self.clock.us, 5_995_000)
    def test_frame_budget_not_extended_for_every_byte(self):
        source = self.source((0, b'\x41'), (2_000_000, b'\x05'), (4_000_000, b'\x00'))
        self.assertEqual(self.receive(source)[0], 255)
        self.assertLessEqual(self.clock.us, 3_005_000)
    def test_actual_controller_errors_are_unchanged(self):
        for address, hexdata in ((0x5100, '06 41 06 03 01 51 00 01 04 60'),
                                 (0x160d, '06 41 06 03 01 16 0d 01 04 32')):
            packet = bytes.fromhex(hexdata)
            self.assertEqual(self.receive(self.source((0, packet)), True), (3, address, bytearray(packet)))
        self.assertEqual(self.errors, [False, False])
    def test_nack_and_eot_keep_existing_recovery_contract(self):
        self.assertEqual(self.receive(self.source((0, b'\x15')), True)[0], 0x15)
        self.assertEqual(self.receive(self.source((0, b'\x04')))[0], 0x41)
        self.assertEqual(self.errors, [True, True])
    def test_invalid_length_and_unknown_response_start(self):
        self.assertEqual(self.receive(self.source((0, b'\x41\x04')))[0], 0xfd)
        self.assertEqual(self.receive(self.source((0, b'\x07')), True)[0], 0x20)
    def test_bad_checksum_does_not_consume_following_frame(self):
        bad = bytearray(frame()); bad[-1] ^= 1
        good = frame(0x930b)
        source = self.source((0, bad + good))
        self.assertEqual(self.receive(source)[0], 0xfe)
        self.assertEqual(self.receive(source), (1, 0x930b, bytearray(good)))
    def test_serial_read_failure(self):
        class Broken:
            def read(self, size): raise OSError('disconnected')
            def read_all(self): raise OSError('disconnected')
        self.assertEqual(self.receive(Broken())[0], 0xaa)
        self.assertEqual(self.errors, [True])
    def listener(self):
        events = []
        module = load('tested_listener', 'viconn_util.py', self.deps | {
            'vs12_adapter': NS(receive_telegr=self.parser.receive_telegr),
            'c_logging': NS(viconnlog=NS(do_log=lambda *a:events.append(a))),
        })
        return module, events
    def test_coalesced_requests_survive_listener_handoff(self):
        listener, _ = self.listener()
        packets = [frame(0x930a), frame(0x930b), frame(0x930c)]
        source = self.source((0, b''.join(packets)))
        delivered = []
        # Delayed main-loop consumer runs only when the producer yields.
        def consume(_):
            delivered.append(listener.get_vicon_request())
            if len(delivered) == len(packets): listener.exit_flag = True
        listener.time = NS(sleep=consume)
        listener.listen_to_Vitoconnect(source)
        self.assertEqual(delivered, packets)
        self.assertFalse(source.buffer)
        self.assertEqual(listener.get_vicon_request(), bytearray())
    def test_listener_wait_can_be_cancelled_without_overwrite(self):
        listener, _ = self.listener()
        pending = frame()
        listener.vicon_request = bytearray(pending)
        listener.time = NS(sleep=lambda _:setattr(listener, 'exit_flag', True))
        source = self.source((0, frame(0x930b)))
        listener.listen_to_Vitoconnect(source)
        self.assertEqual(listener.get_vicon_request(), pending)
        self.assertEqual(len(source.chunks), 1)
    def test_listener_idle_timeout_recovery_is_unchanged(self):
        listener, events = self.listener()
        with self.assertRaisesRegex(Exception, 'Error ff'):
            listener.listen_to_Vitoconnect(self.source())
        self.assertEqual([e[1] for e in events], ['TO 1', 'X ff'])
        self.assertEqual(listener.get_vicon_request(), b'\x04')

if __name__ == '__main__': unittest.main(verbosity=2)
