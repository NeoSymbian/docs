#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read a DTB without publishing its contents or device identifiers.

Output is configuration evidence, never a hardware-probe or driver-readiness claim.
Only explicitly selected peripheral compatibles are emitted. No external tools needed.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

PARTS = {
    'sony,imx355': 'front-camera', 'sony,imx363': 'rear-camera',
    'ti,drv2624': 'haptics', 'nxp,nxp-nci-i2c': 'nfc',
    'qcom,wcn3990-bt': 'bluetooth', 'qcom,wcn3990-wifi': 'wifi',
    'qcom,pm660-rradc': 'battery-adc', 'qcom,pmi8998-fg': 'fuel-gauge',
    'qcom,sdm670-tsens': 'thermal', 'qcom,sdm670-camss': 'camera-controller',
}


def inspect(data):
    if len(data) < 40:
        raise ValueError('truncated DTB header')
    magic, total, off_struct, off_strings, _, version, compat, _, strings_len, struct_len = struct.unpack_from('>10I', data)
    if magic != 0xd00dfeed or version < 17 or compat > 17:
        raise ValueError('expected DTB version 17 compatible header')
    if total > len(data) or total < 40:
        raise ValueError('invalid DTB total size')
    for start, size in ((off_struct, struct_len), (off_strings, strings_len)):
        if start < 40 or start > total or size > total - start:
            raise ValueError('DTB block outside declared file')
    if off_struct % 4 or not (off_struct + struct_len <= off_strings or off_strings + strings_len <= off_struct):
        raise ValueError('unaligned or overlapping DTB blocks')
    strings = data[off_strings:off_strings + strings_len]
    block = data[off_struct:off_struct + struct_len]
    cursor, stack, nodes = 0, [], []
    ended = False
    while cursor + 4 <= len(block):
        token, = struct.unpack_from('>I', block, cursor)
        cursor += 4
        if token == 1:
            end = block.find(b'\0', cursor)
            if end < 0:
                raise ValueError('unterminated node name')
            name = block[cursor:end].decode('ascii')
            cursor = (end + 4) & ~3
            node = {'name': name, 'properties': {}, 'parent': stack[-1] if stack else None}
            if not stack and nodes:
                raise ValueError('multiple roots')
            nodes.append(node)
            stack.append(node)
        elif token == 2:
            if not stack:
                raise ValueError('unexpected end node')
            stack.pop()
        elif token == 3:
            if not stack or cursor + 8 > len(block):
                raise ValueError('property outside node or truncated')
            length, nameoff = struct.unpack_from('>2I', block, cursor)
            cursor += 8
            end = strings.find(b'\0', nameoff)
            if nameoff >= len(strings) or end < 0 or length > len(block) - cursor:
                raise ValueError('invalid property bounds')
            name = strings[nameoff:end].decode('ascii')
            if name in stack[-1]['properties']:
                raise ValueError('duplicate property')
            stack[-1]['properties'][name] = block[cursor:cursor + length]
            cursor = (cursor + length + 3) & ~3
        elif token == 4:
            pass
        elif token == 9:
            if stack or not nodes:
                raise ValueError('unclosed or missing root')
            ended = True
            break
        else:
            raise ValueError('unknown DTB token')
    if not ended:
        raise ValueError('missing DTB end token')
    found = []
    for node in nodes:
        props = node['properties']
        compatibles = props.get('compatible', b'').rstrip(b'\0').decode('ascii').split('\0')
        selected = next((c for c in compatibles if c in PARTS), None)
        if not selected:
            continue
        enabled, ancestor = True, node
        while ancestor:
            status = ancestor['properties'].get('status', b'okay\0').rstrip(b'\0')
            enabled = enabled and status in (b'okay', b'ok')
            ancestor = ancestor['parent']
        found.append({'part': PARTS[selected], 'compatible': selected,
                      'configured_enabled': enabled})
    return {'schema_version': 1, 'evidence': 'dtb-configuration-only',
            'dtb_sha256': hashlib.sha256(data).hexdigest(),
            'devices': sorted(found, key=lambda d: (d['part'], d['compatible']))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dtb', type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.dtb.read_bytes())
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        parser.exit(1, f'inspect-bonito: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
