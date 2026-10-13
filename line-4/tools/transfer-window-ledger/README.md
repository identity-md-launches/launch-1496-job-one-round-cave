# Transfer-window ledger

See every observed address's incoming, outgoing and signed net token flows in
one bounded Ethereum ERC-20 Transfer window. This Python standard-library tool
revalidates the capture's raw logs and anchors using the inherited strict
crosscheck, then produces address-sorted exact totals. ZTO is the demo token;
captures from the ancestor's IMD reader also work.

From the repository root, one command demonstrates it offline:

```sh
python3 -B line-4/tools/transfer-window-ledger/ledger.py --demo
```

Tried on 2026-10-13: the retained real ZTO window at blocks
26177298–26177309 contains three transfers touching four addresses. A fresh
read of that same range at 03:23:30 UTC through the worker's provided mainnet
relay also returned three events, four addresses and matching anchors. The
public source is recorded as https://ethereum-rpc.publicnode.com per the
assignment's relay attribution rule. `live-zto.json` contains that dated
capture; `live-report.json` contains its derived ledger. The relay address is
not retained. The inherited reader sent its dedicated User-Agent and used
only allowlisted public JSON-RPC reads.

Try the fresh retained evidence without network access:

```sh
python3 -B line-4/tools/transfer-window-ledger/ledger.py --capture line-4/tools/transfer-window-ledger/live-zto.json
```

Each row gives an address, first/last observed block, unique touching-event
count, incoming/outgoing counts, self-transfer count and exact quantities.
All amount integers are JSON decimal strings, with a separate exact token-unit
display; no floating-point arithmetic is used. Self-transfers touch an address
once, appear in both directions and contribute zero net. Zero-valued events
still count. Zero address remains an explicitly marked event endpoint, rather
than silently dropping mint/burn-shaped logs or identifying it as a holder.
No contract behavior or ownership is inferred.

The sum of all received amounts equals the sum of all sent amounts, including
zero address. `sum_net_raw` is therefore zero by construction. This identity
does **not** detect omitted provider logs. Event totals may count tokens again
as they move through multiple addresses. These are window flows, not balances,
holder rankings, swaps, pool volume, full history or proof of finality or
provider honesty. A transfer to PoolManager does not identify the ZTO pool.

Twelve regression tests passed:

```sh
python3 -B line-4/tools/transfer-window-ledger/test_ledger.py
```

The tests compare every real-demo row with the ancestor's native address
summary and cover duplicate/reordered delivery, self-transfers, zero endpoints,
totals exceeding uint256, signed display, empty windows, zero-value events,
removed logs, exact-type tampering, bounded reads, duplicate JSON keys and
refusal of paths outside the workspace before opening them. Mutated fixtures
are synthetic checks, distinct from the retained real-chain observations.

The tool reads only selected workspace JSON and sibling Python modules, makes
no network request and accesses no environment, key or wallet. Inputs are capped
at 16 MiB; the inherited validator enforces 2,000 blocks and 20,000 raw logs.
Keep the sibling `transfer-window-activity`, `transfer-crosscheck` and
`erc20-transfer-window` folders with this tool. No installation is needed.
