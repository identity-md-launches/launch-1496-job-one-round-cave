"""Offline receiver checks, including rehashed lies and read-only landing."""
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import ledger_handoff as kit

RAW = (kit.HERE / 'examples/zto-window.json').read_bytes()


def files(data):
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        return {name: source.read(name) for name in source.namelist()
                if name != 'HANDOFF.json'}


def rebuilt(capture):
    window = kit.ledger.window
    events, duplicates = window.validate_logs(capture['raw_logs'], capture['decimals'],
        capture['token_address'], capture['from_block'], capture['to_block'])
    capture['transfers'] = events
    capture['transfer_count'] = len(events)
    capture['duplicate_count'] = duplicates
    return kit.canonical(capture)


class Tests(unittest.TestCase):
    def test_real_evidence_determinism_exact_bytes_and_no_network(self):
        with patch.object(kit.ledger.window, 'rpc', side_effect=AssertionError('network')):
            data = kit.build(RAW)
            self.assertEqual(data, kit.build(RAW))
            result = kit.inspect_bytes(data)
        self.assertEqual(files(data)[kit.CAPTURE], RAW)
        self.assertEqual(result['ledger']['transfer_count'], 3)
        self.assertEqual(result['ledger']['address_count'], 4)
        self.assertEqual(result['ledger']['sum_net_raw'], '0')
        self.assertFalse(result['trusted_digest_matched'])
        self.assertFalse(result['network_used'])

    def test_rehashed_false_ledger_is_rejected(self):
        payload = files(kit.build(RAW))
        report = kit.parse(payload[kit.REPORT])
        report['addresses'][0]['received_raw'] = '1'
        payload[kit.REPORT] = kit.canonical(report)
        lie = kit.writer.build(payload)
        kit.inspector.inspect_stream(io.BytesIO(lie))
        with self.assertRaisesRegex(ValueError, 'recomputed'):
            kit.inspect_bytes(lie)

    def test_raw_evidence_tampering_rejected(self):
        for field, value in [('removed', True), ('address', kit.ledger.window.TOKENS['imd'])]:
            capture = kit.parse(RAW)
            capture['raw_logs'][0][field] = value
            with self.subTest(field=field), self.assertRaises(kit.ledger.window.RpcError):
                kit.build(kit.canonical(capture))

    def test_event_float_boolean_and_duplicate_json_keys_rejected(self):
        capture = kit.parse(RAW)
        capture['transfers'][0]['block'] = float(capture['transfers'][0]['block'])
        with self.assertRaises(ValueError):
            kit.build(kit.canonical(capture))
        capture = kit.parse(RAW)
        capture['raw_logs'][0]['transactionIndex'] = '0x1'
        capture = kit.parse(rebuilt(capture))
        capture['transfers'][0]['transaction_index'] = True
        with self.assertRaises(kit.ledger.window.RpcError):
            kit.build(kit.canonical(capture))
        for raw in (b'{"x":1,"x":2}', b'NaN', b'1e400', b'1.0', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                kit.parse(raw)

    def test_duplicate_logs_and_order_keep_same_ledger(self):
        capture = kit.parse(RAW)
        capture['raw_logs'].reverse()
        capture['raw_logs'].append(copy.deepcopy(capture['raw_logs'][0]))
        self.assertEqual(kit.recompute(RAW), kit.recompute(rebuilt(capture)))

    def test_self_transfers_and_totals_above_uint256(self):
        capture = kit.parse(RAW)
        sender = capture['raw_logs'][0]['topics'][1]
        for event in capture['raw_logs']:
            event['topics'][1] = sender
            event['topics'][2] = sender
            event['data'] = '0x' + format(2**256 - 1, '064x')
        report = kit.inspect_bytes(kit.build(rebuilt(capture)))['ledger']
        self.assertEqual(report['address_count'], 1)
        row = report['addresses'][0]
        self.assertEqual(row['received_raw'], str(3 * (2**256 - 1)))
        self.assertEqual(row['sent_raw'], row['received_raw'])
        self.assertEqual(row['net_raw'], '0')
        self.assertEqual(row['touching_count'], 3)

    def test_empty_imd_and_zto(self):
        for token in ('imd', 'zto'):
            capture = kit.parse(RAW)
            capture.pop('address_window_summary', None)
            capture['token'] = token.upper()
            capture['token_address'] = kit.ledger.window.TOKENS[token]
            capture['raw_logs'] = []
            report = kit.inspect_bytes(kit.build(rebuilt(capture)))['ledger']
            self.assertEqual(report['addresses'], [])
            self.assertEqual(report['event_total_raw'], '0')

    def test_digest_payload_contract_and_archive_size(self):
        data = kit.build(RAW)
        digest = hashlib.sha256(data).hexdigest()
        self.assertTrue(kit.inspect_bytes(data, digest)['trusted_digest_matched'])
        with self.assertRaises(ValueError):
            kit.inspect_bytes(data, 'a' * 64)
        payload = files(data)
        for name in (kit.CAPTURE, kit.REPORT):
            changed = dict(payload)
            del changed[name]
            with self.assertRaises(ValueError):
                kit.inspect_bytes(kit.writer.build(changed))
        with self.assertRaises(ValueError):
            kit.inspect_bytes(kit.writer.build(dict(payload, extra=b'x')))
        with self.assertRaises(ValueError):
            kit.inspect_bytes(b'x' * (kit.MAX_BYTES + 1))

    def test_read_only_landing_and_standalone_cli(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ledger-handoff-', dir=scratch) as raw:
            stage = Path(raw)
            shutil.copytree(kit.HERE, stage / 'kit', ignore=shutil.ignore_patterns('__pycache__'))
            (stage / 'capture.json').write_bytes(RAW)
            command = [sys.executable, '-B', 'kit/ledger_handoff.py']
            def run(*args):
                return subprocess.run(command + list(args), cwd=stage,
                                      capture_output=True, text=True, timeout=20)
            self.assertEqual(run('demo').returncode, 0)
            packed = run('pack', 'capture.json', 'ledger.zip')
            self.assertEqual(packed.returncode, 0, packed.stderr)
            digest = json.loads(packed.stdout)['archive_sha256']
            result = run('check', 'ledger.zip', '--sha256', digest, '--destination', 'received')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['landing']['ready'])
            self.assertFalse((stage / 'received').exists())
            (stage / 'received/evidence').mkdir(parents=True)
            occupied = stage / 'received/evidence/window.json'
            occupied.write_bytes(b'public existing content')
            result = run('check', 'ledger.zip', '--destination', 'received')
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)['landing']['ready'])
            self.assertEqual(occupied.read_bytes(), b'public existing content')
            (stage / 'link').symlink_to('received')
            self.assertEqual(run('check', 'ledger.zip', '--destination', 'link').returncode, 2)
            for args in [('pack', 'capture.json', 'ledger.zip'),
                         ('check', '../outside'), ('check', 'ledger.zip', '--sha256', 'bad'),
                         ('check', 'ledger.zip', '--destination', '../outside')]:
                rejected = run(*args)
                self.assertEqual(rejected.returncode, 1, rejected.stderr)
                self.assertEqual(rejected.stdout, '')
                self.assertNotIn('Traceback', rejected.stderr)
            (stage / 'symlink.zip').symlink_to('ledger.zip')
            self.assertEqual(run('check', 'symlink.zip').returncode, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
