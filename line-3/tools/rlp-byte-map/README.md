# Map the bytes of an unsigned EIP-1559 envelope

`byte_map.py` shows the exact byte offsets of the type byte, RLP envelope,
all nine unsigned fields, and every access-list address and storage key in
**original** type-2 transaction bytes. Each location distinguishes the RLP
prefix from its payload. A worker can inspect a serialized proposal byte by
byte, including duplicate access-list entries, without guessing where a field
begins. The unchanged sibling decoder validates the complete unsigned envelope
first, so signed, legacy, malformed, noncanonical and trailing bytes are refused.

One command from the repository root shows it working:

```sh
python3 -B line-3/tools/rlp-byte-map/byte_map.py --demo
```

Tried locally: exit 0; the inherited synthetic 46-byte ZTO `totalSupply()`
sample mapped its type byte, list prefix and nine contiguous fields. The
20-byte destination payload occupies the exact supplied ZTO address bytes,
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`. This is an offline
inspection sample, not a captured or executed transaction. No chain state is
claimed.

Pass a complete hexadecimal envelope as one argument or with `--stdin`.
Hex may have a lowercase `0x` prefix. Standard input accepts one trailing
newline. Output is JSON with schema `rlp-byte-map/v1`, exact byte offsets,
the inherited decoded transaction, and a SHA-256 fingerprint of the unsigned
input bytes. The fingerprint is **not** an Ethereum transaction hash, a
signature or sender identity. Offsets are zero-based; `endByteExclusive` is
excluded. For a literal byte below `0x80`, RLP has no prefix and the prefix
length is zero. The `envelope` location starts just after the type byte.

Malformed input exits 2, writes a short error to stderr, and emits no partial
JSON. The inherited 128 KiB transaction and 16,384-item bounds apply. Mapping
is only byte structure: it does not establish available nonce or balance, token
behavior, execution result, inclusion, gas sufficiency or safety. Python
standard library only; keep the committed `../zto-eip1559-decoder/` sibling
beside this folder. The tool does not read files or environment variables,
use a key or wallet, sign, send, pay or post, and requires no network.

Checks tried:

```sh
python3 -B -m unittest discover -s line-3/tools/rlp-byte-map -v
```

Four behavioral tests cover the demonstration's original byte slices,
long-form RLP and duplicate nested access-list slots, malformed and signed
envelopes, and CLI success/failure without partial output. All four passed.

## Round 33 mark

**The Nested Stone:** Pepe finds smaller stones inside a hollow stone, as a
worker sees nested byte ranges inside an envelope. A small charcoal, ochre and
chalk pigment mark sits on vacant upper-right rock. The inherited Pepe and
all earlier pigment remain; the mark adds no hands or hand stencils.
