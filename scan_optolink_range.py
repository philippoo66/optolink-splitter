#!/usr/bin/env python3
import argparse
import socket
import sys
import time
from typing import Iterable, List, Tuple, Optional


def readline(sock: socket.socket, timeout: float = 1.5) -> str:
    sock.settimeout(timeout)
    data = b""
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        if ch in (b"\r", b"\n"):
            break
        data += ch
    return data.decode(errors="ignore").strip()


def parse_hex_or_dec(value: str) -> int:
    value = value.strip().lower()
    base = 16 if value.startswith("0x") else 10
    return int(value, base)


def match_value(
    hex_field: str,
    length: int,
    any_endian: bool,
    target: Optional[int] = None,
    value_range: Optional[Tuple[int, int]] = None,
) -> bool:
    v = hex_field.lower()
    try:
        # Normalize hex string length for the given byte length
        needed = length * 2
        v_clean = v.lstrip("0x")
        v_clean = v_clean.rjust(needed, "0")[-needed:]
        raw = int(v_clean, 16)
    except Exception:
        return False

    def in_targets(x: int) -> bool:
        if target is not None and x == target:
            return True
        if value_range is not None:
            lo, hi = value_range
            if lo <= x <= hi:
                return True
        return False

    if in_targets(raw):
        return True

    if any_endian and length in (2, 4):
        # Swap endianness at 16-bit granularity
        if length == 2:
            swapped = int(v_clean[2:4] + v_clean[0:2], 16)
        else:
            swapped = int(v_clean[6:8] + v_clean[4:6] + v_clean[2:4] + v_clean[0:2], 16)
        return in_targets(swapped)

    return False


def scan(
    host: str,
    port: int,
    ranges: List[Tuple[int, int]],
    length: int,
    target: Optional[int],
    value_range: Optional[Tuple[int, int]] = None,
    success_codes: Iterable[str] = ("0", "1"),
    delay: float = 0.0,
    any_endian: bool = True,
    print_all: bool = False,
    print_matching_code: bool = False,
) -> List[Tuple[int, str]]:
    hits: List[Tuple[int, str]] = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect((host, port))
        for start, end in ranges:
            for a in range(start, end + 1):
                cmd = f"read;0x{a:04X};{length};'raw'\n"
                s.sendall(cmd.encode())
                line = readline(s)
                if not line:
                    continue
                parts = line.split(";")
                if len(parts) != 3:
                    continue
                code, value_hex = parts[0], parts[2]
                if print_all:
                    print(f"READ 0x{a:04X} -> {line}")
                elif print_matching_code and code in success_codes:
                    print(f"READ 0x{a:04X} -> {line}")
                if code not in success_codes:
                    continue
                if match_value(
                    value_hex,
                    length=length,
                    any_endian=any_endian,
                    target=target,
                    value_range=value_range,
                ):
                    hits.append((a, line))
                if delay > 0:
                    time.sleep(delay)
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
    return hits


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Scan Optolink TCP for an address range and search for a target value in a single session."
    )
    ap.add_argument("start", help="Start address (e.g. 0x0EE0 or 3808)")
    ap.add_argument("end", help="End address inclusive (e.g. 0x0F40)")
    ap.add_argument("length", type=int, choices=[1, 2, 4], help="Number of bytes to read")
    ap.add_argument(
        "value",
        nargs="?",
        help="Target value to match (decimal or 0x.. hex). Optional when --value-range is used",
    )
    ap.add_argument("--host", default="localhost", help="Optolink TCP host (default: %(default)s)")
    ap.add_argument("--port", type=int, default=65234, help="Optolink TCP port (default: %(default)s)")
    ap.add_argument(
        "--codes",
        default="0,1",
        help="Comma-separated list of success codes to accept (default: 0,1)",
    )
    ap.add_argument(
        "--no-any-endian",
        action="store_true",
        help="Disable matching both endiannesses for multi-byte values",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Optional delay in seconds between requests (default: 0.0)",
    )
    ap.add_argument(
        "--print-all",
        action="store_true",
        help="Print every address response during the scan",
    )
    ap.add_argument(
        "--print-matching-code",
        action="store_true",
        help="Print only responses whose code matches --codes",
    )
    ap.add_argument(
        "--value-range",
        metavar="START:END",
        help="Inclusive range of values to match (decimal or hex, e.g. 10:20 or 0x0A:0x14)",
    )

    args = ap.parse_args(argv)
    start = parse_hex_or_dec(args.start)
    end = parse_hex_or_dec(args.end)
    if end < start:
        start, end = end, start

    target: Optional[int] = parse_hex_or_dec(args.value) if args.value else None
    vr: Optional[Tuple[int, int]] = None
    if args.value_range:
        try:
            s, e = args.value_range.split(":", 1)
            lo, hi = parse_hex_or_dec(s), parse_hex_or_dec(e)
            if hi < lo:
                lo, hi = hi, lo
            vr = (lo, hi)
        except Exception as exc:
            print(f"Invalid --value-range '{args.value_range}': {exc}", file=sys.stderr)
            return 2
        # When a range is provided, ignore the single target value
        target = None
    codes = tuple(c.strip() for c in args.codes.split(",") if c.strip())
    any_endian = not args.no_any_endian

    ranges = [(start, end)]
    hits = scan(
        host=args.host,
        port=args.port,
        ranges=ranges,
        length=args.length,
        target=target,
        value_range=vr,
        success_codes=codes,
        delay=args.delay,
        any_endian=any_endian,
        print_all=args.print_all,
        print_matching_code=args.print_matching_code,
    )
    if hits:
        print("HITS:")
        for a, line in hits:
            print(f"0x{a:04X} -> {line}")
    else:
        print("No hits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
