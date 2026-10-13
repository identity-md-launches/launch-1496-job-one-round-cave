#!/usr/bin/env python3
"""Offline regression checks for snapshot-seal."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).with_name('snapshot_seal.py')
spec = importlib.util.spec_from_file_location('snapshot_seal', SOURCE)
seal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seal)
EXAMPLE = Path(__file__).parents[1] / 'pinned-snapshot' / 'example-zto.json'


class SnapshotSealTests(unittest.TestCase):
    def write(self, directory, name, value):
        path = Path(directory) / name
        path.write_text(json.dumps(value, indent=2) + '\n')
        return path

    def test_seal_is_deterministic_and_has_pinned_facts(self):
        first = seal.seal(EXAMPLE)
        self.assertEqual(first, seal.seal(EXAMPLE))
        self.assertEqual(first['schema'], 'pinned-zto-seal/1')
        self.assertEqual(first['observation']['token'], seal.pinned.ZTO)
        self.assertEqual(first['observation']['block_number'], '26177368')

    def test_verify_accepts_exact_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = self.write(directory, 'receipt.json', seal.seal(EXAMPLE))
            self.assertTrue(seal.verify(EXAMPLE, receipt)['verified'])

    def test_verify_rejects_changed_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = seal.seal(EXAMPLE)
            receipt['observation']['block_number'] = '0'
            receipt_path = self.write(directory, 'receipt.json', receipt)
            with self.assertRaises(ValueError):
                seal.verify(EXAMPLE, receipt_path)

    def test_rejects_non_pinned_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = self.write(directory, 'not-pinned.json', {'schema': 'nope'})
            with self.assertRaises(ValueError):
                seal.seal(snapshot)

    def test_rejects_malformed_receipt_json(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'receipt.json'
            receipt.write_text('{')
            with self.assertRaises(ValueError):
                seal.verify(EXAMPLE, receipt)


if __name__ == '__main__':
    unittest.main()
