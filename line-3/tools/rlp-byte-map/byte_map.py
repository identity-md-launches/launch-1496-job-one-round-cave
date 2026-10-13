#!/usr/bin/env python3
"""Locate each field and access-list item in original unsigned type-2 RLP."""

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "zto-eip1559-decoder"))
import tx_decode as decoder

NAMES = ("chainId", "nonce", "maxPriorityFeePerGas", "maxFeePerGas",
         "gasLimit", "to", "value", "data", "accessList")
MAX_INPUT_CHARS = 2 * decoder.MAX_TRANSACTION_BYTES + 2


def _node(raw, start, limit, budget):
    """Walk already validated canonical RLP, retaining prefix and payload spans."""
    budget[0] -= 1
    if budget[0] < 0 or start >= limit:
        raise ValueError("RLP map exceeds item bounds")
    first = raw[start]
    if first < 0x80:
        payload_start, end, is_list = start, start + 1, False
    else:
        is_list = first >= 0xc0
        short_base = 0xc0 if is_list else 0x80
        long_base = 0xf7 if is_list else 0xb7
        if first <= long_base:
            length = first - short_base
            payload_start = start + 1
        else:
            length_size = first - long_base
            length_start = start + 1
            length_end = length_start + length_size
            if length_end > limit:
                raise ValueError("truncated RLP length")
            length = int.from_bytes(raw[length_start:length_end], "big")
            payload_start = length_end
        end = payload_start + length
    if end > limit:
        raise ValueError("RLP item exceeds parent")
    children = []
    if is_list:
        cursor = payload_start
        while cursor < end:
            child = _node(raw, cursor, end, budget)
            children.append(child)
            cursor = child["endByteExclusive"]
        if cursor != end:
            raise ValueError("RLP children do not fill parent")
    return {"startByte": start, "prefixByteLength": payload_start - start,
            "payloadStartByte": payload_start,
            "payloadByteLength": end - payload_start,
            "endByteExclusive": end,
            "kind": "list" if is_list else "bytes", "children": children}


def _location(path, node):
    return {"path": path, **{key: value for key, value in node.items()
                             if key != "children"}}


def inspect(transaction_hex):
    """Map original bytes after the inherited strict unsigned decoder accepts them."""
    transaction = decoder.decode(transaction_hex)
    stripped = transaction_hex[2:] if transaction_hex.startswith("0x") else transaction_hex
    raw = bytes.fromhex(stripped)
    root = _node(raw, 1, len(raw), [decoder.MAX_RLP_ITEMS])
    if root["kind"] != "list" or len(root["children"]) != 9 or root["endByteExclusive"] != len(raw):
        raise ValueError("unsigned envelope does not fill original bytes")
    locations = [{"path": "typeByte", "startByte": 0, "prefixByteLength": 0,
                  "payloadStartByte": 0, "payloadByteLength": 1,
                  "endByteExclusive": 1, "kind": "bytes"},
                 _location("envelope", root)]
    for name, node in zip(NAMES, root["children"]):
        locations.append(_location(name, node))
        if name != "accessList":
            continue
        for index, entry in enumerate(node["children"]):
            base = f"accessList[{index}]"
            locations.append(_location(base, entry))
            locations.append(_location(base + ".address", entry["children"][0]))
            slots = entry["children"][1]
            locations.append(_location(base + ".storageKeys", slots))
            for slot_index, slot in enumerate(slots["children"]):
                locations.append(_location(base + f".storageKeys[{slot_index}]", slot))
    return {"schema": "rlp-byte-map/v1", "byteLength": len(raw),
            "sha256Fingerprint": hashlib.sha256(raw).hexdigest(),
            "locations": locations, "transaction": transaction}


def main(args):
    if args == ["--demo"]:
        source = decoder.demo_transaction()
    elif args == ["--stdin"]:
        source = sys.stdin.read(MAX_INPUT_CHARS + 1).removesuffix("\n").removesuffix("\r")
    elif len(args) == 1 and not args[0].startswith("--"):
        source = args[0]
    else:
        print("usage: byte_map.py --demo | --stdin | '0x02...'", file=sys.stderr)
        return 2
    try:
        result = inspect(source)
    except (ValueError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
