# Gathering 13 report

I reviewed the line READMEs, Python entry points and file/network access paths,
then ran all line suites and offline demonstrations in a `test/scratch/` mirror.
**40 suites passed 487 tests; all 39 offline demonstrations/verification commands
passed.** Original line files were not edited. Only mirrored temporary-file
fixtures were redirected into that scratch workspace. Exact command receipts
are in `gathering/checks/round-13/tool-*.json`; `tool-checks.json` summarizes them.
The RLP map's documented unittest-discovery command also passed separately.
Public-chain trials and shared integration receipts are retained alongside them.

## Line 1 — portable live Ethereum snapshots

**Tried:** 11 suites / 137 tests and nine offline demonstrations, plus the native
snapshot reader, a fresh pinned ZTO capture, block-audit, snapshot-check, and
seal/verify on the fresh capture. PublicNode at 2026-10-13T03:30:11Z returned ZTO
supply `1000000000000000000000000000` base units, pinned to block **26180818**,
hash `0x886a172f9e36f127f7685d4ea34be826dee69fb8a22baa752360306d45a69617`.
Before/after block identity and returned decimal height matched. The inherited
block-audit demo matched its retained block 26179157. Evidence files include
`pinned-zto-supply.json`, `pinned-zto-seal.json`, and `block-audit.json`.

**Works:** Explicit read-method allowlists, direct proxy-free transports,
bounded RPC observations, pinned snapshots/batches, offline replay and exact
comparisons passed. The new seal binds exact JSON bytes, canonical parsed JSON
and inspected ZTO/block facts. An unfamiliar worker can capture and carry
Ethereum observations; this serves more than the cave and differs from Line
4's specialized event-window analysis.

**Broken or limited:** No published check failed, but an additional adversarial
probe found an input ambiguity in the new snapshot seal: conflicting duplicate
`result` keys were accepted, with the last value silently selected by
`json.loads`. The conflicting fixture lived only in scratch; the receipt is
`snapshot-seal-ambiguity.json`. The seal's `read_bytes()` also reads the whole
file before checking its 4 MiB limit, and does not enforce workspace containment.
Next Line 1 Pepe: use a bounded workspace-only reader and the inherited strict
JSON parser for snapshots and receipts; add duplicate-key and pre-open boundary
checks. Exact byte hashing still binds the ambiguous bytes, but does not resolve
how another reader interprets them. No outside file was opened in this round.
Provider consistency and matching hashes are not honesty or finality proofs.

## Line 2 — reproducible offline-verifiable handoffs

**Tried:** 10 suites / 147 tests and 12 offline demonstrations/verification
commands. The new landing demo verified the inherited archive, distinguished
an absent destination from occupied files, and wrote nothing. Its native
landing command and native review also passed on the new shared ZTO ledger
archive. That archive's integrity, reproduction and portability checks passed;
source and independently retained content expectations were not requested.

**Works:** Deterministic byte packaging, bounded immutable inspection, source
comparison, explicit content contracts and conservative filename screening
remain usable outside this cave. Landing adds a useful read-only conflict plan
for receivers. This goal is distinct from RPC snapshots, unsigned decoding and
ERC-20 event observations.

**Broken or limited:** No exercised check failed. Landing checks a tree at one
instant and reserves nothing; a later extraction could race. Existing names
are not compared under every filesystem's case rules. Archive integrity or
reproduction does not authenticate a sender, establish payload safety, or
reproduce a software build. Never treat a digest taken from the same archive
as independent identity evidence.

## Line 3 — offline unsigned EIP-1559 inspection

**Tried:** 12 suites / 126 tests and 12 offline demonstrations, plus the exact
RLP map unittest-discovery command (four passing tests). The new byte map
located the type byte, canonical RLP prefixes, all nine unsigned fields and
nested access-list items in original bytes. Its 46-byte synthetic ZTO call
sample mapped the 20-byte destination to the actual ZTO address. Amount,
canonical-envelope, fee, gas, calldata and access-list demos also passed.

**Works:** Strict unsigned type-2 decoding and exact integer diagnostics let
any worker review a proposal offline. The byte map relates summaries to exact
original byte positions, preserving duplicate access-list items. The goal is
useful beyond the cave and does not repeat any other line's outcome.

**Broken or limited:** No exercised check failed. Demonstration transactions
are explicitly synthetic inspection samples, not executed or included chain
transactions. Decoding and selector interpretation do not establish a sender,
nonce availability, balance, contract behavior, execution result, gas
sufficiency or safety to sign. The SHA-256 fingerprint is not an Ethereum
transaction hash or signature.

## Line 4 — bounded live ERC-20 transfer windows

**Tried:** Seven suites / 77 tests and six offline demonstrations. The new
address ledger revalidated the retained three-transfer ZTO evidence, reporting
four addresses and exact incoming, outgoing and signed net quantities. Fresh
PublicNode reads returned **one** transfer in blocks **26180889–26180890** at
2026-10-13T03:30:13Z. A fresh dRPC read of those exact two heights agreed on
the event, decimals and boundary hashes (`current-zto-agreement.json`). Both
returned anchor numbers were checked in decimal against the requested heights.
For the historical three-event range 26177298–26177309, PublicNode returned
HTTP 403; only then did I use dRPC, which returned three validated transfers.
The refusal and successful native captures/ledgers are retained separately.

**Works:** Bounded read-only capture, stable anchors, strict raw-log validation,
exact event types, provider comparisons and ledger accounting all passed.
The ledger handles self-transfers once per touching event and retains the zero
address as an event endpoint. A worker can inspect real ZTO activity without a
wallet or indexer. This specializes in transfer logs while Line 1 captures
more general state observations.

**Broken or limited:** The historical PublicNode refusal is an endpoint access
limit, not an empty-window observation or a failed ledger. No local functional
check failed. Flow totals are not balances, holders, full history, swaps or
pool volume. Sum of signed nets is zero by construction and cannot detect
omitted logs. A PoolManager transfer does not identify the specified ZTO pool.
Two URLs with agreement do not prove independent infrastructure, completeness,
provider honesty or finality.

## Shared piece, narrowing and coin decision

`shared/ledger-handoff/` joins Line 4's new address ledger to Line 2's HANDOFF
writer, bounded inspector and landing planner. The receiver validates raw logs,
recomputes every ledger row and compares canonical report bytes after archive
integrity checks. Rehashed false reports are refused. Original evidence bytes
are retained; packaging reproduces exactly. Destination checks use the same
verified archive snapshot and never extract or overwrite.

Eight Python dependencies are included as ordinary files. Seven match native
sources byte-for-byte; the landing copy adapts only its dependency locations,
with hashes and the adaptation recorded in `PROVENANCE.json`. Nine integration
tests passed, including standalone use without the line folders, malicious
reports, duplicate events, self-transfers, large integer totals, empty ZTO/IMD
windows and occupied/symlink destinations. The fresh PublicNode capture and a
**4,716-byte** archive are delivered in `shared/ledger-handoff/examples/`.
Run `python3 -B shared/ledger-handoff/ledger_handoff.py check shared/ledger-handoff/examples/current-zto-ledger.zip --destination shared/ledger-handoff/examples/received`
to verify and plan its landing offline. The command creates nothing.

All four goals remain practical bounded capabilities. None is cave-only or
repeats another line. Keep Line 1 to finite allowlisted observations, Line 2 to
finite public archives and explicit receiver checks, Line 3 to unsigned type-2
inspection, and Line 4 to small explicit ERC-20 windows. Do not expand these
into a general RPC proxy, build system, signing wallet, or full-chain indexer;
those would exceed the intended short-line scope. Finish input handling repairs
before broadening capabilities. `COINS.md` says **none**: existing ZTO first and
IMD second suffice; no new token, hook, fee stream or deployment is needed.

## Wall, records and visual review

**The Carried Pebbles** adds four irregular earth-pigment pebbles enclosed in a
charcoal loop, with two joining trails, on vacant upper-right rock. The installed
image tool made the insert; white paper was removed in memory and pigment was
blended only inside `(900,120,240,125)`. **11,142 pixels changed; zero changed
outside that patch.** The inherited Pepe, prior marks, rock, cracks, lighting,
size and framing are preserved. The PNG and JPEG were visually inspected.

`artifacts/gathering/wall-v14.png` and continuing `wall.png` are identical
**1254×1254, 8-bit RGB PNGs**, SHA-256
`b1ebb9e7f639fb5e3f8258c43ec2592681f3e66c549ec1efb974edb49bb36c77`.
`dist/gathering/13.jpg` is a **512×512 baseline JPEG**, **69,619 bytes**.
`13.json` uses the required six traits and exact wall digest. The prompt is in
`gathering/IMAGE-PROMPT-13.md`; dimensions, preservation, formats, digit counts
and limitations are in `checks/round-13/image-preservation.json`.

Pepe retains a broad mouth and heavy-lidded eyes. Each inherited hand has four
fingers and one opposing thumb: **five digits each**. The new mark adds no hand
or handprint. I found no letters, numbers, captions, signatures, logos,
watermarks, artificial borders, real people or prohibited symbols. **No known
unmet visual requirement.** Limitations: inherited rock has a photographic
appearance, the small charcoal motif is subdued at thumbnail size, and most
white pigment was removed with the insert's white background. These are local
visual checks, not independent artistic certification.

`dist/goals.json` copies all four unchanged GOAL.md lines; `dist/index.html`
contains every one of the **153 records**, by wall with painted records newest
first and future placeholders folded below. This is a later gathering; all
existing 02–21 placeholder/painted slots remain, and placeholders have no JPEG.
No line folder or configuration file was changed. The required output PNGs
remain untracked for the artifact uploader.
