#!/usr/bin/env python3
"""Carry validated ERC-20 address flows and plan a non-overwriting landing."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

HERE = Path(__file__).resolve().parent
MAX_BYTES = 99_000
CAPTURE = 'evidence/window.json'
REPORT = 'review/ledger.json'
SCHEMA = 'erc20-ledger-handoff/1'


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / 'vendor' / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ledger = load('ledger_handoff_ledger', 'transfer-window-ledger/ledger.py')
writer = load('ledger_handoff_writer', 'handoff/handoff.py')
inspector = load('ledger_handoff_inspector', 'handoff-inspect/inspect_handoff.py')
landing = load('ledger_handoff_landing', 'handoff-landing/landing.py')
LIMITS = inspector.Limits(archive_bytes=MAX_BYTES, payload_bytes=MAX_BYTES,
                         manifest_bytes=4096, metadata_bytes=4096, files=2)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def reject_number(value):
    raise ValueError('floating point and non-finite JSON numbers are refused')


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON exceeds 99000 bytes')
    return json.loads(raw.decode('utf-8'),
                      object_pairs_hook=ledger.activity.no_duplicate_object,
                      parse_float=reject_number, parse_constant=reject_number)


def recompute(raw):
    return ledger.report(parse(raw))


def inspect_bytes(data, expected=None, destination=None):
    """Verify one immutable archive, then derive its report and landing plan."""
    if destination is not None:
        landing.destination_parts(destination)
    receipt = inspector.inspect_stream(io.BytesIO(data), LIMITS, expected)
    if {item['path'] for item in receipt['files']} != {CAPTURE, REPORT}:
        raise ValueError('exact evidence and ledger payloads required')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = {item['path']: archive.read(item['path']) for item in receipt['files']}
    if writer.build(files) != data:
        raise ValueError('archive does not reproduce under the original writer')
    report = recompute(files[CAPTURE])
    if files[REPORT] != canonical(report):
        raise ValueError('saved ledger differs from recomputed raw logs')
    result = {'schema': SCHEMA, 'verified': True, 'network_used': False,
              'archive_sha256': receipt['archive_sha256'],
              'archive_bytes': receipt['archive_bytes'],
              'trusted_digest_matched': receipt['trusted_digest_matched'],
              'capture_bytes_sha256': hashlib.sha256(files[CAPTURE]).hexdigest(),
              'byte_reproducible': True, 'ledger_recomputed': True,
              'ledger': report,
              'limitations': 'Integrity and event accounting only; not sender identity, '
              'balances, completeness, finality, provider honesty or payload safety. '
              'Landing is a read-only point-in-time plan, never extraction or reservation.'}
    if destination is not None:
        result['landing'] = landing.plan_receipt(receipt, destination)
    return result


def build(raw):
    report = recompute(raw)
    data = writer.build({CAPTURE: raw, REPORT: canonical(report)})
    inspect_bytes(data)
    return data


def read_workspace(raw):
    return writer.regular_bytes(writer.workspace_path(raw), MAX_BYTES)


def demo():
    raw = (HERE / 'examples/zto-window.json').read_bytes()
    data = build(raw)
    if data != build(raw):
        raise ValueError('nondeterministic packaging')
    result = inspect_bytes(data)
    result['demo'] = 'Dated real ZTO evidence; no network, file writes or extraction.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    pack = commands.add_parser('pack')
    pack.add_argument('capture')
    pack.add_argument('archive', help='new workspace-relative ZIP; never overwritten')
    check = commands.add_parser('check')
    check.add_argument('archive')
    check.add_argument('--sha256', help='independently trusted archive SHA-256')
    check.add_argument('--destination', help='plain workspace-relative landing directory')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'pack':
            target = writer.workspace_path(args.archive, must_exist=False)
            data = build(read_workspace(args.capture))
            result = inspect_bytes(data)
            with target.open('xb') as output:
                output.write(data)
            result['output'] = args.archive
        else:
            result = inspect_bytes(read_workspace(args.archive), args.sha256, args.destination)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if 'landing' in result and not result['landing']['ready'] else 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, UnicodeError,
            RecursionError, OverflowError, zipfile.BadZipFile, EOFError,
            NotImplementedError, struct.error):
        print('ledger-handoff: invalid, over-limit or inconsistent evidence; no receipt emitted',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
