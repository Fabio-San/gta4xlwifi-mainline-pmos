# KNOWN_ISSUES.md — Functional status and improvement plan

This is the technical reference for the porting state: **what works**, **what works partially**, **what does not work**, and **how it could be fixed**. Each entry is based on field evidence.

> Italian: [KNOWN_ISSUES.it.md](KNOWN_ISSUES.it.md)

---

## 1. Functional matrix

| Feature | Status | Evidence | Possible fix |
|---|---|---|---|
| Mainline 7.3 boot via uniLoader | ✅ Verified | boot `d71a7d11`, XFCE starts | — |
| DSI display 1200×2000 @ 67Hz | ✅ | modeset OK, panel detected | — |
| Xorg modesetting + DRI3 + Panfrost | ✅ | renderer `Mali-G72 MC3 (Panfrost)` | — |
| DPU zero-copy (CMA) | ✅ Technical | `DPP+0x40 = 0xd3a00000`, buffer with real pixels | see #1 |
| Touchscreen Himax HX83102E | ✅ | SPI, events OK | — |
| WiFi | ✅ | `scsc_wlbt`, mx140 firmware | — |
| Stereo speaker audio (TAS2562) | ✅ | AABox/UAIF0, stereo playback | see #2 |
| Headphone jack | ⚠️ Partial | UAIF0 branch, `HEADPHONE Switch`, `jd-src=<1>` | physical test with headphones (never done) |
| Persistent volume, clock | ✅ | Verified | — |
| Poweroff/reboot (PS_HOLD) | ✅ | `0x330c` | — |
| Battery / charging | ✅ | Verified | — |
| SSH | ✅ | Disabled by default, can be enabled | — |
| **Video smoothness (YouTube/Chromium)** | ⚠️ Partial | zero-copy active but not perceived | #1 |
| **Audio perceived "2×"** | ⚠️ Not measured | — | #2 |
| **Native microphone** | ❌ | Calliope/DSP | #3 |
| **MFC / HW video decode** | ❌ | incompatible firmware | #4 |
| **Bluetooth** | ❌ | missing `scsc_bt` | #5 |
| **GPU encoder / video encode** | ❌ | see #4 | #4 |
| **PageFlip** | ⚠️ Not retested | `Option "PageFlip" "false"` | #6 |
| **CPU/GPU clocks** | ⚠️ Low | schedutil, GPU ~260 MHz | #7 |

---

## 2. Details and how to approach them

### #1 — Video smoothness (GPU / zero-copy)
Panfrost + DPU zero-copy work technically (CMA buffer with real pixels), but no clear improvement was perceived on YouTube/Chromium. Possible causes: PageFlip disabled, browser still copying frames, low GPU clock.
**How to fix**: 1) try `Option "PageFlip" "true"` (not retested after zero-copy); 2) test with `mpv --vo=gpu`; 3) measure FPS with `glxgears`/`perf`.

### #2 — Audio perceived "2×"
Reported by user on YouTube, never measured.
**How to fix**: during playback run `cat /proc/asound/card0/pcm0p/sub0/hw_params` (rate, channels, format); check `pactl list sinks` for a double path (ABOX + TAS2562); check for 44.1→48 kHz resampling.

### #3 — Native microphone (blocked)
WDMA/SPUM/Calliope investigated; capture requires unavailable Calliope DSP firmware. Bare-metal attempts exhausted. Not solvable with mainline alone.

### #4 — MFC: HW video decode/encode (blocked)
`s5p-mfc` probes (`ip_ver = 0x1202`, MFC v12.02) but Lineage `mfc_fw.bin` (renamed `s5p-mfc-v10.fw`) is incompatible → `s5p_mfc_wait_for_done_dev: command:12 timed out`. Node removed from DTS to stop the loop.
**How to fix**: obtain compatible `s5p-mfc-v12.fw`, or port the downstream `exynos/mfc` driver (~1 MB / 58 files, userspace-incompatible). Not recommended.

### #5 — Bluetooth
`scsc_wlbt` loads (WiFi OK), but `scsc_bt` driver is missing. Port it from the 4.14 kernel.

### #6 — PageFlip
`Option "PageFlip" "false"` in Xorg, never retested after zero-copy. Try `true` and measure.

### #7 — CPU/GPU clocks
Governor `schedutil`, GPU devfreq ~260 MHz. Check ACPM DVFS; optionally use `performance` governor for testing.

---

## 3. Work log

See `docs/WORKLOG.md` for the detailed porting chronology.
