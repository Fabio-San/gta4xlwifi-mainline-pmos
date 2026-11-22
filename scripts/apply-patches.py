#!/usr/bin/env python3
"""Apply kernel patches in order, verifying SHA256 where a manifest exists."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KDIR = ROOT / "sources" / "linux-7.3"
PATCHES = ROOT / "patches"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_dir(d):
    if not d.exists():
        return 0
    patches = sorted(d.glob("*.patch"))
    if not patches:
        return 0
    manifest = d / "import-sha256.json"
    known = json.loads(manifest.read_text()) if manifest.exists() else {}
    count = 0
    for p in patches:
        # Skip patches already applied (dry-run reverse)
        rev = subprocess.run(
            ["patch", "-p1", "-d", str(KDIR), "--dry-run", "-R"],
            stdin=p.open("rb"), capture_output=True,
        )
        if rev.returncode == 0:
            print(f"  skip (already applied): {p.name}")
            continue
        digest = sha(p)
        if p.name in known and known[p.name] != digest:
            print(f"WARNING: {p.name} SHA256 differs from manifest", file=sys.stderr)
        res = subprocess.run(
            ["patch", "-p1", "-d", str(KDIR)],
            stdin=p.open("rb"), capture_output=True,
        )
        if res.returncode != 0:
            print(f"FAILED applying {p.name}:\n{res.stderr.decode(errors='replace')}", file=sys.stderr)
            sys.exit(1)
        print(f"  applied: {p.name}")
        count += 1
    return count


def main():
    if not (KDIR / "Makefile").exists():
        sys.exit("Kernel not found. Run scripts/setup-build-env.sh first.")
    total = 0
    for sub in sorted(PATCHES.iterdir()):
        if sub.is_dir():
            total += apply_dir(sub)
    total += apply_dir(PATCHES)
    print(f"Patches applied: {total}")


if __name__ == "__main__":
    main()
