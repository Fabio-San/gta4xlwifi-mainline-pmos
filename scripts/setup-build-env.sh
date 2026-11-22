#!/bin/bash
# Prepare the build environment: clone kernel 7.3 and apply patches.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KDIR="$ROOT/sources/linux-7.3"

echo "=== Checking dependencies ==="
for t in git python3 make gcc aarch64-linux-gnu-gcc cpio gzip xz dtc; do
  command -v "$t" >/dev/null 2>&1 || echo "WARNING: $t not found (install crossbuild-essential-arm64 device-tree-compiler)"
done

if [ ! -d "$KDIR/.git" ]; then
  echo "=== Cloning kernel 7.3 ==="
  mkdir -p "$ROOT/sources"
  git clone --depth 1 -b v7.3 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git "$KDIR"
else
  echo "=== Kernel already present ==="
fi

echo "=== Applying patches ==="
python3 "$ROOT/scripts/apply-patches.py"

echo "=== Setup complete ==="
