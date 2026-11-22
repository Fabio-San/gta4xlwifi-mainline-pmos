# gta4xlwifi-mainline-pmos

Mainline Linux 7.3 + postmarketOS (XFCE) for the **Samsung Galaxy Tab S6 Lite LTE (SM-P610 / gta4xlwifi, Exynos 9611)**.

This repository contains:
- the kernel sources, patches and config used for the boot image,
- scripts to build and flash the `boot.img` safely,
- a builder for a **sterile, bootable ROM** (no personal data),
- full documentation: build, flash, hardware map and known limitations.

> **Status**: experimental configuration, not a production ROM.
> The kernel and rootfs described here were used and verified in the field on an
> SM-P610; the *sterile ROM* is prepared from this configuration but **has not been
> tested as a final package** (see [Known issues](docs/KNOWN_ISSUES.md)).
> Always read [FLASH.md](docs/FLASH.md) before touching the device.

> Italian version: [README.it.md](README.it.md)

---

## What works (field-verified)

| Feature | Status | Notes / details |
|---|---|---|
| Mainline 7.3 boot via uniLoader | ✅ | no bootloader / vbmeta flashing |
| XFCE UI (modesetting + Panfrost) | ✅ | DRI3, DPU zero-copy |
| WiFi | ✅ | `scsc_wlbt` driver, `mx140` firmware |
| Stereo speaker audio (TAS2562) | ✅ | AABox/UAIF0 — [ROADMAP §4](docs/ROADMAP.md#4-audio--playback-already-works-polish-and-verification) |
| Headphone jack | ⚠️ | UAIF0 branch, never physically tested — [ROADMAP §4](docs/ROADMAP.md#4-audio--playback-already-works-polish-and-verification) |
| Network / SSH | ✅ | **disabled by default**, can be enabled (see below) |
| Poweroff / reboot | ✅ | PS_HOLD |
| Persistent volume, clock | ✅ | |
| Touchscreen | ✅ | Himax HX83102E over SPI |
| Battery / charging | ✅ | |
| **GPU / video smoothness** | ⚠️ | Panfrost + zero-copy work, not smooth on YouTube — [ROADMAP §3](docs/ROADMAP.md#3-gpu--full-acceleration-encoding--metal--video) |
| **Native microphone** | ❌ | needs Calliope/DSP firmware — [ROADMAP §2](docs/ROADMAP.md#2-microphone-native-capture--calliope-dsp) |
| **MFC (HW video decode/encode)** | ❌ | firmware incompatible, disabled in DTS — [ROADMAP §3](docs/ROADMAP.md#3-gpu--full-acceleration-encoding--metal--video) |
| **Bluetooth** | ❌ | needs `scsc_bt` driver port — [ROADMAP §1](docs/ROADMAP.md#1-bluetooth--scsc_bt-driver-port) |

For the full action plan with evidence and steps, see [ROADMAP.md](docs/ROADMAP.md)
([Italiano](docs/ROADMAP.it.md)). Current limitations: [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).
MMIO map: [HARDWARE.md](docs/HARDWARE.md).

---

## Quick start

### Build the boot.img

```bash
git clone https://github.com/Fabio-San/gta4xlwifi-mainline-pmos.git
cd gta4xlwifi-mainline-pmos
git checkout pmos
bash scripts/setup-build-env.sh          # install deps + clone kernel 7.3
bash scripts/build-upstream.sh           # produces artifacts/boot.img
```

See [BUILD.md](docs/BUILD.md) for details.

### Flash

```powershell
# Windows, from Lineage Recovery, with automatic backup:
.\scripts\flash-boot-adb.ps1 -Image .\artifacts\boot.img -Serial <SERIAL>
```

Or build the complete sterile ROM:

```bash
bash scripts/make-sterile-rom.sh /path/to/local-rootfs-backup.tar.gz
# -> release/gta4xlwifi-pmos-7.3-<date>.zip
```

The zip is **not committed to git**: it is published as a GitHub **Release** with a
tag such as `v7.3-pmos-YYYYMMDD`. The repository only holds sources, scripts and docs.

See [FLASH.md](docs/FLASH.md) and [STERILE-ROM.md](docs/STERILE-ROM.md).

---

## Sterile ROM — account and SSH

| Item | Value |
|---|---|
| Default user | `gta4xlwifi` |
| Default password | `147147` |
| Virtual keyboard | `onboard`, auto-started, large keys |
| SSH | **NOT started at boot** |
| Enable SSH | "SSH" icon in the XFCE menu (GUI) or `sudo rc-service sshd start` (terminal) |

> **⚠️ CHANGE THE PASSWORD IMMEDIATELY** after the first login:
> run `passwd` in a terminal, or XFCE Settings → Users.
> The default password is public: do not expose the device on a network until changed.

---

## Safety (always read)

- **NEVER flash the `bootloader` partition** (nor `vbmeta`): the device may be bricked.
- Do not use Odin for `boot` unless you know exactly what you are doing: use the ADB script from recovery.
- **Always back up** `boot`, `dtbo`, `recovery`, `vbmeta` before any flash (the script does it automatically).
- This repo contains **no personal data**: no WiFi passwords, MAC addresses, serials, user files or keys.
- The sterile ROM regenerates `machine-id` and SSH host keys on first boot.

---

## Repository layout

```
.
├── README.md / README.it.md
├── docs/
│   ├── BUILD.md / BUILD.it.md          # kernel + boot.img build
│   ├── FLASH.md / FLASH.it.md          # safe flash and rollback
│   ├── HARDWARE.md / HARDWARE.it.md    # MMIO map, firmware, DTS (hardware only)
│   ├── KNOWN_ISSUES.md / KNOWN_ISSUES.it.md
│   ├── WORKLOG.md / WORKLOG.it.md
│   ├── AI_WORKFLOW.md / AI_WORKFLOW.it.md
│   └── STERILE-ROM.md / STERILE-ROM.it.md
├── configs/upstream/                   # .config + touch fragment
├── patches/upstream/                   # kernel patches
├── tools/                              # pmos-init, busybox, adbd, setup-rndis
├── scripts/                            # build, flash, patch-reapply, ROM builder
└── device/                             # ssh-toggle, first-boot, onboard config
```

---

## Credits

This work is the result of collaboration between a human and several AI assistants.

- **Fabio-San** — idea, direction, hardware, time, energy, field testing and decisions.
- **Hy4 flash Free (OpenCode)** — the main engineering work: kernel debugging, DTS,
  display/audio/MFC investigation, initramfs and chroot work, sterile ROM builder,
  documentation and repo.
- **Gemini 4 Hydrogen** — deep analysis of mount propagation, GSettings/systemd issues,
  MFC firmware and hardware registers.
- **ChatGPT Luna 6** and **Antigravity** — additional reasoning and cross-checks.

Thanks also to the **postmarketOS** and **mainline Linux** communities for the
Exynos 9610/9611 bring-up, the authors of the patches in `patches/upstream/`
(each header carries original authorship) and the **gta4xl** community for DTS,
display and power ground work.

See [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md) for how to keep working with AI assistants on this project.

---

## License

- Code and documentation written for this repo: **MIT** (see [LICENSE](LICENSE)).
- Linux kernel and kernel patches: **GPL-2.0** (sources included, as required).
- Binaries in `tools/`: their respective licenses (busybox GPL-2.0, adbd Apache-2.0, pmos-init GPL-2.0).

See [NOTICE.md](NOTICE.md) for the full breakdown.
