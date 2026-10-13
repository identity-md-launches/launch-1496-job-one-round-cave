# Snapshot Seal

Make a deterministic, offline-verifiable receipt for a saved `pinned-zto-snapshot/1` observation. The receipt binds both the exact JSON bytes and the canonical JSON form to the observation's inspected Ethereum block identity, ZTO address, and exact `totalSupply()` quantity. It gives a worker a compact handoff check without opening a network connection.

From the repository root, this command works offline and prints a receipt for the retained real ZTO observation:

```sh
python3 -B line-1/tools/snapshot-seal/snapshot_seal.py seal line-1/tools/pinned-snapshot/example-zto.json
```

I ran it against the included PublicNode observation from `2026-10-12T16:02:50Z`; it reported block `26177368`, hash `0xf76539e08b42037cad963c2af646774753fce06ad37245bd1487b9e6ffa549ba`, the real ZTO address, and supply `1000000000000000000000000000` base units. To save and later verify a receipt, redirect the `seal` output and use `verify SNAPSHOT RECEIPT`; both operations are offline.

Run the offline checks with:

```sh
python3 -B line-1/tools/snapshot-seal/test_snapshot_seal.py
```

The tool reuses the sibling `pinned-snapshot` inspector, so it refuses malformed, changed-chain, changed-call, or inconsistent-before/after block snapshots before producing a receipt. A matching receipt establishes byte and structural consistency only. It is not a signature, proof of provider honesty, independent corroboration, finalization proof, current-state claim, or permission to sign or send anything. Standard-library Python only; it never accesses a key, wallet, secret, environment setting, or network.
