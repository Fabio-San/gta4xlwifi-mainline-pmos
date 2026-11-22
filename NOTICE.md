# NOTICE.md — Licenses and attribution

| Component | License | Notes |
|---|---|---|
| Scripts in `scripts/`, configs, docs (except where noted) | MIT | Copyright (c) 2026 Fabio-San. See [LICENSE](LICENSE). |
| Linux kernel sources (`sources/linux-7.3`, fetched by build script) | GPL-2.0 | Fetched from kernel.org; not vendored in this repo. |
| Kernel patches in `patches/upstream/`, `patches/upstream-wifi/` | GPL-2.0 | Each patch header carries original authorship/email. Inherited from the kernel. |
| `tools/pmos-init-aarch64` | GPL-2.0 | From postmarketOS (`pmos-init`), SHA256 `2f87e1be…`. |
| `tools/busybox-aarch64` | GPL-2.0 | BusyBox. |
| `tools/adbd-aarch64` | Apache-2.0 | Android adbd. |
| `tools/setup-rndis.sh` | MIT | From the gta4xl bring-up scripts. |
| `tools/hwctl-aarch64` | GPL-2.0 | Hardware control helper from the bring-up tree. |
| `scripts/build.py`, `scripts/upstream/init`, `scripts/upstream/desktop-test` | MIT | Build/initramfs helpers from the gta4xl bring-up tree. |

## Attribution

- **postmarketOS** project — initramfs/init design.
- **mainline Linux** community and the authors of the Exynos 9610/9611 patches
  (see patch headers for names and emails).
- **gta4xl** community — DTS, display and power ground work.

## No personal data

This repository and the sterile ROM contain no personal data from the original
author: no device serial, MAC addresses, IP addresses, WiFi passwords, user files,
SSH keys or GPG keys. Hardware-only addresses are documented in
[HARDWARE.md](docs/HARDWARE.md).
