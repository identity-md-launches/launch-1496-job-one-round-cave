# Ledger handoff

Carry exact per-address ERC-20 event flows to another worker in a reproducible
HANDOFF v1 archive. The receiver validates the original raw logs, recomputes
every ledger row, and can check a destination for conflicts without extracting
anything. This joins Line 4's address ledger with Line 2's packaging, inspection,
filename screening and landing planner. It uses only Python's standard library;
the entire folder works without the line folders, installation or network.

From the repository root, one command demonstrates it offline:

```sh
python3 -B shared/ledger-handoff/ledger_handoff.py demo
```

Tried: the retained real ZTO observation at blocks 26177298–26177309 produced
three transfers and four address rows, with exact signed net amounts. Its bytes
are retained unchanged in `examples/zto-window.json`. This is dated provider
evidence, not a fabricated transaction or current-chain claim.

A fresh PublicNode ZTO observation at 2026-10-13T03:30:13Z returned one transfer
in blocks 26180889–26180890. Its original JSON bytes and an actual 4,716-byte
archive are included. Check the complete receiver path offline:

```sh
python3 -B shared/ledger-handoff/ledger_handoff.py check shared/ledger-handoff/examples/current-zto-ledger.zip --destination shared/ledger-handoff/examples/received
```

This reports a ready destination without creating it. Existing files, file or
symlink ancestors, and file/directory collisions produce a diagnostic with
exit 2; no files are overwritten. Exit 1 refuses invalid input and emits no
partial receipt. Exit 0 means the requested checks passed. `--sha256 HASH`
accepts an independently trusted archive digest; a hash obtained from the same
archive only checks self-consistency.

To package a small public capture from the native transfer-window reader:

```sh
python3 -B shared/ledger-handoff/ledger_handoff.py pack shared/ledger-handoff/examples/current-zto-window.json test/scratch/new-ledger.zip
```

Create `test/scratch/` first for that example. Output uses exclusive creation;
an existing archive is refused. Input and archive limits are 99,000 bytes.
Only the exact `evidence/window.json` and canonical `review/ledger.json`
payloads are accepted. Duplicate JSON keys, floats, non-finite values, changed
event summaries, altered ledger amounts, missing/extra payloads and incompatible
ZIP serialization are refused. Input file paths stay inside the selected
workspace and reject symlinks. Selected inputs must contain public data only.

Nine behavioral tests passed, including standalone CLI use, rehashed false
reports, malformed raw evidence, duplicate logs, empty ZTO/IMD windows,
self-transfers, exact totals above uint256, occupied destinations and refusal
of symlinks or outside paths:

```sh
python3 -B shared/ledger-handoff/test_ledger_handoff.py
```

The included fresh archive also passed Line 2's native landing and format
review commands. Eight dependencies are vendored as ordinary files with hashes
in `PROVENANCE.json`. Seven match their line source byte-for-byte; the landing
module only changes where its two Python dependencies are resolved. Its
destination checks still use the caller's workspace. The native landing demo
references its original line fixture and is not a public entry point here.

Flows are Transfer-event accounting within one provider window, not balances,
holder rankings, complete history, swaps or pool volume. In/out conservation
holds by construction and cannot detect omitted logs. A PoolManager transfer
does not identify the ZTO pool. Verification does not authenticate a sender,
prove provider honesty or finality, or certify execution or payload safety.
Landing is a point-in-time plan, with no extraction or atomic reservation;
existing names are not compared under every filesystem's case rules. The tool
reads no environment, wallet, key or secret, and never signs, sends or posts.
