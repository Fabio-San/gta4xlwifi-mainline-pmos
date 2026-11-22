# BUILD.md — Building kernel 7.3 and boot.img

This document explains how to rebuild the `boot.img` used on gta4xlwifi from scratch.

> Italian: [BUILD.it.md](BUILD.it.md)

## Prerequisites

- WSL2 with Ubuntu/Debian, or native Linux x86_64
- ~10 GB free disk space
- Tools: `git`, `python3`, `build-essential`, `crossbuild-essential-arm64`,
  `device-tree-compiler`, `cpio`, `gzip`, `xz-utils`, `curl`, `wget`, `openssl`,
  `adb`, `fastboot` (Windows side for flashing)

```bash
sudo apt update
sudo apt install -y git python3 build-essential crossbuild-essential-arm64 \
  device-tree-compiler cpio gzip xz-utils curl wget openssl \
  clang lld llvm bison flex libssl-dev
```

If your distro provides only a versioned clang (e.g. `clang-21`), make sure an
unversioned `clang` and `ld.lld` exist on PATH (the build uses `LLVM=1`):
```bash
sudo ln -sf /usr/bin/clang-21 /usr/local/bin/clang
sudo ln -sf /usr/bin/ld.lld-21 /usr/local/bin/ld.lld
```

> **Important**: clone/build in a directory whose path contains **no spaces**.
> The kernel Makefile's `O=` output handling breaks on paths with spaces
> (e.g. `Ubuntu Project`). Use something like `~/gta4xlwifi-mainline-pmos`.

## 1. Workspace setup

```bash
git clone https://github.com/Fabio-San/gta4xlwifi-mainline-pmos.git
cd gta4xlwifi-mainline-pmos
git checkout pmos
bash scripts/setup-build-env.sh
```

`setup-build-env.sh` clones the 7.3 kernel into `sources/linux-7.3` (if missing),
applies patches from `patches/upstream/` and `patches/upstream-wifi/`, and verifies
patch hashes (`import-sha256.json`).

Required build files (all included in this repo): `tools/upstream-init-aarch64`
(the original `pmos-init`, SHA256 `2f87e1be…`), `tools/hwctl-aarch64`,
`tools/busybox-aarch64`, `tools/adbd-aarch64`, `tools/setup-rndis.sh`,
`scripts/build.py`, `scripts/upstream/init` and `scripts/upstream/desktop-test`.
`build-upstream.py` downloads the pinned kernel tarball and UniLoader automatically
and creates `sources/` on first run.

Manual clone:

```bash
mkdir -p sources
git clone --depth 1 -b v7.3 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git sources/linux-7.3
python3 scripts/apply-patches.py
```

## 2. Configuration

Config: `configs/upstream/gta4xl.config` (327 lines) plus the touch fragment
`configs/upstream/92-mainline-himax.conf`.

Key points:
- `CONFIG_MODULES=y` — modules are packed into the rootfs
- `CONFIG_DRM_EXYNOS9610` / Panfrost / DPU zero-copy enabled
- **MFC disabled**: the `mfc@12c30000` node was removed from the DTS (see
  `scripts/reapply-kernel-patches.sh`). The mainline driver loads an incompatible
  firmware and spams warnings every 2 seconds; do not re-enable it.

## 3. Build

```bash
bash scripts/build-upstream.sh
# or manual:
python3 scripts/build-upstream.py --slot boot --no-fallback \
  --variant peripherals --persistent --jobs "$(nproc)"
```

The script:
1. builds `Image`, DTB and modules,
2. builds the embedded initramfs from `tools/` (pmos-init + busybox + adbd),
3. creates the boot.img with uniLoader (Android header v2, 2048-byte pages),
4. writes `artifacts/boot-upstream-peripherals-nofallback-persistent.img`,
5. emits a JSON with hashes (kernel, dtb, initramfs).

## 4. Verify output

```bash
sha256sum artifacts/boot-upstream-peripherals-nofallback-persistent.img
```

Current known-good boot image SHA256:

```
d71a7d110e93ca35aecbcc51baa72f1daf0eb39fc5fa7e38a38f2a3bda5f1212
```

It contains `pmos-init-aarch64` with SHA256:

```
2f87e1be573923cd333700ba9f8c1959d7cdbcce0656bcaa7b2aeb81462052b8
```

## 5. Known build issues

- **"Failed to write database /usr/lib/udev/hwdb.bin: Function not implemented"**:
  benign error inside a WSL chroot; does not block the build.
- **MFC**: if you rebuild from "dirty" sources (MFC node still in DTS) you get a
  boot that spams `s5p_mfc_wait_for_done_dev` every 2 seconds. Run
  `bash scripts/reapply-kernel-patches.sh` before rebuilding.
- **uniLoader**: the boot image uses uniLoader with the init **embedded in the
  kernel**: editing the outer Android ramdisk has no effect. Always act on
  `tools/pmos-init-aarch64` and rebuild.
