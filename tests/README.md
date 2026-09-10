# VS2 receive regression tests

Run the deterministic tests from the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

These use the standard library, a simulated nonblocking serial port and a
simulated monotonic clock. They load the production parser and listener modules
with configuration, logging and MQTT dependencies replaced. No local settings
file, broker or physical device is required.

The tests cover fragmented frames at every byte boundary, a first byte arriving
near the idle deadline, multiple frames arriving together, raw forwarding,
checksum failures, decoded payloads, bounded timeouts, controller error replies
and pending-request handoff/cancellation.

The receiver assumes nonblocking serial ports, as configured by the splitter.
It waits up to three seconds for the first byte, then allows a separate three
seconds to assemble the frame (including the ACK for responses). Later bytes do
not extend that assembly deadline. It reads only the current frame, leaving
subsequent frames in the serial input buffer. The listener waits until the main
loop consumes the pending request before reading another one.

On Linux, additionally run the integration checks using the project's existing
`pyserial` dependency:

```sh
python3 tests/serial_integration.py
```

These open temporary pseudo-terminals, not physical serial ports. They check
coalesced frames, a fragmented frame that crosses the original idle deadline,
and ordered handoff between actual listener and consumer threads. The timing
check takes approximately three seconds and depends on OS scheduling; the unit
tests provide deterministic deadline coverage.

To compare the same deterministic tests against another checkout, set
`OPTOLINK_TEST_ROOT` to that checkout's absolute path. The old implementation
fails the late-frame and coalesced-frame regression cases.
