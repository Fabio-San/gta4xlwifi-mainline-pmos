#!/bin/bash
# Convenience wrapper around the real build script (from the bring-up tree).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f "$ROOT/sources/linux-7.3/Makefile" ]; then
  echo "Kernel sources missing. Run: bash scripts/setup-build-env.sh" >&2
  exit 1
fi

# The upstream build script expects the kernel tree at sources/linux-7.3
# relative to the project root, matching this repository layout.
python3 "$ROOT/scripts/build-upstream.py" \
  --slot boot --no-fallback --variant peripherals --persistent \
  --jobs "${JOBS:-$(nproc)}"

echo "Boot image written to artifacts/"
