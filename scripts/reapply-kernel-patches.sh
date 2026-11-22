#!/bin/bash
# Re-apply the board-specific patches after a kernel source update.
# In particular: remove the experimental MFC node from the peripherals DTS.
# Run from anywhere; paths are relative to this repository.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DTS="$ROOT/sources/linux-7.3/arch/arm64/boot/dts/exynos/exynos9610-gta4xl-peripherals.dts"

if [ ! -f "$DTS" ]; then
  echo "DTS not found: $DTS" >&2
  echo "Run scripts/setup-build-env.sh first." >&2
  exit 1
fi

echo "=== Removing experimental MFC node from DTS (if present) ==="
python3 - "$DTS" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
s = p.read_text()
blocks = [
"""\tmfc_clk: mfc-clock {
\t\tcompatible = "fixed-clock";
\t\t#clock-cells = <0>;
\t\tclock-frequency = <400000000>;
\t};

""",
"""\t/* Exynos 9610 MFC v10 (ip_ver 0x1202 from 4.14 DTB) */
\tmfc: mfc@12c30000 {
\t\tcompatible = "samsung,mfc-v10";
\t\treg = <0x0 0x12c30000 0x10000>;
\t\tinterrupts = <GIC_SPI 175 IRQ_TYPE_LEVEL_HIGH>;
\t\tclocks = <&mfc_clk>;
\t\tclock-names = "aclk_mfc";
\t\tdma-coherent;
\t\tstatus = "okay";
\t};

""",
]
changed = False
for b in blocks:
    if b in s:
        s = s.replace(b, "")
        changed = True
p.write_text(s)
print("MFC node removed" if changed else "No MFC node present (nothing to do)")
PY

if grep -q 'mfc@12c30000' "$DTS"; then
  echo "ERROR: MFC node still present" >&2
  exit 1
fi

echo "=== Re-applying patch series ==="
python3 "$ROOT/scripts/apply-patches.py"

echo "=== Done. Rebuild with: bash scripts/build-upstream.sh ==="
