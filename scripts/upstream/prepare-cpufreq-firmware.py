#!/usr/bin/env python3
"""Reproduce the Exynos9610 FVP/TMU binaries from the pinned downstream Intel HEX."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGES = {
    'fvp': (0x9000, 'ef90c09de8aa5685556192eab3bc8ff951682061a0dd19440f85591262ae5dc8'),
    'tmu': (0xa400, '4a0ae12f0b32bd78cc2519b5bffc6c717351f26ec3a3dc5315218adaf533ec58'),
}


def prepare_one(name, base_address, expected_sha):
    source = ROOT / f'sources/kernel/firmware/exynos9610_acpm_{name}.fw.ihex'
    target = ROOT / f'sources/linux-7.3/firmware/exynos9610_acpm_{name}.fw'
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected_sha:
        raise SystemExit('Downstream firmware source checksum mismatch: ' + name)
    data = bytearray()
    base = None
    end = False
    for line in source.read_text().splitlines():
        if not line.startswith(':'):
            raise SystemExit('Invalid Intel HEX record')
        record = bytes.fromhex(line[1:])
        if len(record) != record[0] + 5 or sum(record) & 255:
            raise SystemExit('Invalid Intel HEX length/checksum')
        count, address, kind = record[0], int.from_bytes(record[1:3]), record[3]
        if kind == 1:
            end = True
            break
        if kind == 3 and count == 4:
            continue  # Linker entry address; payload remains contiguous.
        if kind != 0:
            raise SystemExit('Unexpected Intel HEX record type')
        if base is None:
            base = address
        if address != base + len(data):
            raise SystemExit('Non-contiguous firmware')
        data.extend(record[4:4 + count])
    if not end or base != base_address or len(data) != 0x1400 or len(data) % 4:
        raise SystemExit('Unexpected Exynos9610 FVP image layout')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def prepare():
    return {name: prepare_one(name, *args) for name, args in IMAGES.items()}


if __name__ == '__main__':
    print('Exynos9610 ACPM SHA256:', prepare())
