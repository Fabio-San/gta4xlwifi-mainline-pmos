# HARDWARE.md — Hardware map (hardware data only)

This document collects the addresses and values validated in the field.
**No personal data** (no device serial, MAC, WiFi, user IDs).

> Italian: [HARDWARE.it.md](HARDWARE.it.md)

## SoC

- **Exynos 9611** (SM-P610 / gta4xlwifi, Galaxy Tab S6 Lite LTE)
- 4× Cortex-A73 + 4× Cortex-A53, ARMv8.0 (4 KB page size)
- Mali-G72 MP3 GPU (Panfrost, DRI3)

## Validated MMIO addresses

| Block | Address | Notes |
|---|---|---|
| DPU / DECON (display) | `0x14881000`, `0x14891000` | IDMA/DPP, zero-copy CMA |
| DPP base address | `DPP+0x40 = 0xd3a00000` | CMA buffer with real XFCE pixels |
| HSI2C3 (touch / sensors) | `0x11d10000` | Himax HX83102E |
| ABOX (audio) | `0x14a50000` | UAIF0, TAS2562 stereo |
| TAS2562 | via AABox/UAIF0 | stereo playback (`HEADPHONE Switch`, `jd-src=<1>`) |
| PS_HOLD (poweroff) | `0x330c` | shutdown/reboot |
| Calliope (DSP/mic) | `calliope_*.bin` firmware | **native mic blocked**, needs DSP firmware |
| MFC | `0x12c30000` | **disabled in DTS** (incompatible firmware) |

## Display

- DSI panel: **1200×2000 @ 67.051 Hz**, 135×226 mm
- Driver: `exynos9610_drm.c` with `drm_gem_fb_create_with_dirty` (KMS base fix)
- Xorg: `modesetting` + `DRI 3`, `PageFlip false`

## Required firmware (in `/lib/firmware`)

| File | Use |
|---|---|
| `mx140.bin`, `mx140_wlan_sw.hcf` | WiFi |
| `AP_AUDIO_SLSI.bin`, `APBargeIn_AUDIO_SLSI.bin`, `APBiBF_AUDIO_SLSI.bin` | audio |
| `calliope_dram.bin`, `calliope_iva.bin`, `calliope_sram.bin` | DSP (mic not working) |
| ACPM plugins (fvp/tmu) | CPU/GPU DVFS |

The sterile ROM includes hardware firmware; **no personal WiFi configuration**.

## WiFi

- `scsc_wlbt` loads and WiFi works.
- Bluetooth needs the `scsc_bt` driver (not ported).
- The sterile ROM configures **no network**: users enter their own credentials.

## MFC notes (HW video decode)

The mainline `s5p-mfc` driver probes (`ip_ver = 0x1202`, MFC v12.02) but the Lineage
`mfc_fw.bin` (renamed `s5p-mfc-v10.fw`) is incompatible:
`s5p_mfc_wait_for_done_dev: Interrupt (command:12) timed out`.

The node is removed from the DTS to stop the warning loop.
See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
