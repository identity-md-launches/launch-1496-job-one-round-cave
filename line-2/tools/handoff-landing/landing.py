#!/usr/bin/env python3
"""Check where a verified HANDOFF v1 ZIP could land, without extracting it."""

import argparse
import importlib.util
import json
from pathlib import Path
import stat
import sys


def load(name, relative):
    path = Path.cwd()
    for part in Path(relative).parts:
        path /= part
        if path.is_symlink():
            raise ValueError("tool dependency is a symlink")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INSPECT = load("landing_inspect", "line-2/tools/handoff-inspect/inspect_handoff.py")
PORTABILITY = load("landing_portability", "line-2/tools/handoff-portability/portability.py")


def destination_parts(value):
    if (not isinstance(value, str) or not value or value.startswith("/")
            or "\\" in value or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("destination must be a plain workspace-relative directory")
    return value.split("/")


def existing_type(path):
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return "missing"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    return "special"


def first_blocker(components, leaf_file):
    """Inspect only named components; never follow a symlink or read a file."""
    path = Path.cwd()
    for index, component in enumerate(components):
        path /= component
        kind = existing_type(path)
        if kind == "missing":
            return None
        if kind != "directory":
            if kind == "file" and leaf_file and index == len(components) - 1:
                return "existing-file", "/".join(components[:index + 1])
            return kind + ("-at-leaf" if index == len(components) - 1 else "-ancestor"), "/".join(components[:index + 1])
        if leaf_file and index == len(components) - 1:
            return "directory-at-file", "/".join(components)
    return None


def plan_receipt(receipt, destination):
    root_parts = destination_parts(destination)
    root_blocker = first_blocker(root_parts, False)
    files = [item["path"] for item in receipt["files"]]
    occupied = set(files)
    issues = []
    for path in sorted(files):
        parts = path.split("/")
        for end in range(1, len(parts)):
            if "/".join(parts[:end]) in occupied:
                issues.append({"path": path, "kind": "archive-file-as-directory",
                               "blocking_path": "/".join(parts[:end])})
                break
        if root_blocker:
            issues.append({"path": path, "kind": root_blocker[0],
                           "blocking_path": root_blocker[1]})
            continue
        blocker = first_blocker(root_parts + parts, True)
        if blocker:
            issues.append({"path": path, "kind": blocker[0],
                           "blocking_path": blocker[1]})
    portability = PORTABILITY.analyze(files)
    return {
        "format": "handoff-landing-v1",
        "destination": destination,
        "archive_sha256": receipt["archive_sha256"],
        "trusted_digest_matched": receipt["trusted_digest_matched"],
        "file_count": receipt["file_count"],
        "ready": not issues and not portability,
        "path_issues": issues,
        "portability_profile": PORTABILITY.PROFILE,
        "portability_issues": portability,
        "note": "Read-only preflight of named workspace paths at one instant; no extraction, "
                "atomic reservation, sender authentication or payload safety claim. "
                "Existing names on a different case-insensitive filesystem are not checked."
    }


def plan(archive, destination, expected=None):
    destination_parts(destination)
    receipt = INSPECT.inspect_path(archive, expected=expected)
    return plan_receipt(receipt, destination)


def demo():
    archive = "line-2/handoff.zip"
    fresh = plan(archive, "line-2/tools/handoff-landing/unpacked-demo")
    occupied = plan(archive, "line-2/tools/handoff")
    if not fresh["ready"] or occupied["ready"]:
        raise ValueError("inherited archive landing demo did not behave as expected")
    return {"fresh": fresh, "occupied": occupied,
            "demo": "real inherited archive; neither destination was changed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    check = commands.add_parser("check")
    check.add_argument("archive", help="workspace-relative HANDOFF v1 ZIP")
    check.add_argument("destination", help="workspace-relative landing directory")
    check.add_argument("--sha256", help="independently obtained archive SHA-256")
    args = parser.parse_args(argv)
    try:
        result = demo() if args.command == "demo" else plan(
            args.archive, args.destination, args.sha256)
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True))
        return 0 if args.command == "demo" or result["ready"] else 2
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        print("handoff-landing: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
