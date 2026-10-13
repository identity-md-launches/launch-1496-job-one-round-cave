# Handoff Landing

Check whether a fully verified HANDOFF v1 archive can land at a chosen
workspace directory without overwriting anything. The command is read only: it
does not create the directory, extract archive files, or execute their contents.
Python 3.8+ and only its standard library are needed. From the workspace root:

```sh
python3 -B line-2/tools/handoff-landing/landing.py demo
```

The demo verifies the real inherited `line-2/handoff.zip`. It reports a fresh
destination as ready and the inherited source directory as occupied. Neither
destination is changed. To check your own public deliverable:

```sh
python3 -B line-2/tools/handoff-landing/landing.py check line-2/handoff.zip line-2/tools/handoff-landing/unpacked-demo
```

Optional `--sha256 HASH` checks an archive digest obtained independently. Exit
0 means the verified archive has no detected landing conflicts; exit 2 means
valid archive bytes with path or portability issues; exit 1 refuses invalid
input with no partial JSON report. The inherited bounded inspector validates
every ZIP member first. This tool inspects only the target path components,
using `lstat` so it does not follow or read symlinks. It reports an occupied
file, a directory where a file must land, a blocked ancestor, internal
file/directory collisions, and the inherited conservative filename portability
issues. It never reads existing destination file contents.

Keep the existing `line-2/tools/handoff-inspect/inspect_handoff.py` and
`line-2/tools/handoff-portability/portability.py` at those workspace-relative
paths. No network or installed package is needed to run this piece.

When tried, the real archive verified, its new destination was ready and its
occupied source directory was blocked. The local behavior suite covered
existing files and directories, symlinks, ancestor files, internal archive
collisions, corrupt archives, and unsafe destination paths.

This is a point-in-time plan, not a reservation: the tree can change before a
person extracts the archive. It does not perform extraction, protect against
hostile concurrent ancestor replacement, compare existing names under every
destination filesystem's case rules, authenticate the sender, or prove payload
safety. Choose a destination containing public files only; this tool reads
path metadata but no file contents.
