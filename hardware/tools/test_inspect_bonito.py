# SPDX-License-Identifier: Apache-2.0
"""Malformed DTB and evidence-boundary regressions for the inventory reader."""
import importlib.util
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('inventory', Path(__file__).with_name('inspect-bonito.py'))
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def word(n):
    return struct.pack('>I', n)


def node(name):
    data = name.encode() + b'\0'
    return word(1) + data + b'\0' * (-len(data) % 4)


def prop(offset, value):
    return word(3) + word(len(value)) + word(offset) + value + b'\0' * (-len(value) % 4)


def fixture(disabled=False):
    strings = b'compatible\0status\0serial-number\0'
    block = node('') + prop(18, b'PRIVATE-IDENTIFIER\0') + node('bus')
    if disabled:
        block += prop(11, b'disabled\0')
    block += node('haptics@5a') + prop(0, b'ti,drv2624\0') + word(2) * 3 + word(9)
    offset = 56
    header = struct.pack('>10I', 0xd00dfeed, offset + len(block) + len(strings), offset,
                         offset + len(block), 40, 17, 16, 0, len(strings), len(block))
    return header + b'\0' * 16 + block + strings


class InventoryTests(unittest.TestCase):
    def test_only_allowlisted_facts_leave_dtb(self):
        result = inventory.inspect(fixture())
        self.assertEqual(result['evidence'], 'dtb-configuration-only')
        self.assertEqual(result['devices'], [{'part': 'haptics', 'compatible': 'ti,drv2624',
                                              'configured_enabled': True}])
        self.assertNotIn('PRIVATE-IDENTIFIER', str(result))

    def test_disabled_parent_disables_child(self):
        self.assertFalse(inventory.inspect(fixture(True))['devices'][0]['configured_enabled'])

    def test_every_truncation_rejected(self):
        data = fixture()
        for length in range(len(data)):
            with self.subTest(length=length), self.assertRaises(ValueError):
                inventory.inspect(data[:length])

    def test_block_outside_total_rejected(self):
        data = bytearray(fixture())
        struct.pack_into('>I', data, 8, len(data) + 4)
        with self.assertRaises(ValueError):
            inventory.inspect(data)

    def test_unbalanced_node_rejected(self):
        data = bytearray(fixture())
        data[56:60] = word(2)
        with self.assertRaises(ValueError):
            inventory.inspect(data)

    def test_missing_end_rejected(self):
        data = bytearray(fixture())
        end = data.find(word(9), 56)
        data[end:end + 4] = word(4)
        with self.assertRaises(ValueError):
            inventory.inspect(data)


if __name__ == '__main__':
    unittest.main()
