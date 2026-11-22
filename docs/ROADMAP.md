# ROADMAP.md — Action plan for missing hardware features

This document collects the **concrete actions, data and references** needed to finish
the features that do not work yet. It is based on field evidence gathered during the
port, not on speculation. Each item lists what we know, what is missing and the
recommended next step.

> Italian: [ROADMAP.it.md](ROADMAP.it.md)
> Related: [KNOWN_ISSUES.md](KNOWN_ISSUES.md) (current status), [HARDWARE.md](HARDWARE.md) (MMIO map).

---

## 1. Bluetooth — `scsc_bt` driver port

### What we know (evidence)
- The `scsc_wlbt` driver loads and WiFi works.
- The device is the **Samsung SCSC wlbt** combo chip (WiFi + BT).
- No Bluetooth client appears: `hciconfig`/`bluetoothctl` show nothing.
- The missing piece is the **`scsc_bt`** kernel driver, present in the downstream
  4.14 tree but not ported to 7.3.

### What is missing
- `drivers/bluetooth/scsc_bt*` (HCI transport over the shared wlbt link).
- The BT firmware (`bt_fw.bin`) and the device tree binding for the BT side.
- Correct power sequencing / reset GPIO shared with WiFi.

### Recommended steps
1. Locate `scsc_bt` in `/home/fabio/gta4xl-4.14/` (downstream tree, still on WSL):
   ```bash
   find /home/fabio/gta4xl-4.14 -iname '*scsc*bt*'
   ```
2. Compare the 4.14 `scsc_bt` with the already-working 7.3 `scsc_wlbt` port
   (patches in `patches/upstream-wifi/`): reuse the same transport/MMIO mapping.
3. Port `scsc_bt` to 7.3 HCI APIs (`hci_alloc_dev`, `hci_uart` or the vendor
   transport used by wlbt).
4. Add the BT firmware to `/lib/firmware` and the DTS node.
5. Verify: `hciconfig -a`, `bluetoothctl power on`, `bluetoothctl scan on`.

### Risk / effort
Medium. The transport is already proven by WiFi; mostly HCI glue and firmware.

**IMPORTANT discovery:** a prebuilt `scsc_bt.ko` already exists in the author's
tree at `sources/scsc-upstream/scsc_bt.ko` (alongside `scsc_wlan.ko`,
`scsc_mx.ko`, `scsc_platform_mif.ko`). If it was built against this 7.3 tree,
Bluetooth may be closer than expected: check `modinfo sources/scsc-upstream/scsc_bt.ko`
for `vermagic` matching `7.3.0-gta4xl-upstream`, then try `insmod` and `hciconfig -a`
before doing any driver port. The missing part might only be firmware/DTS wiring.

---

## 2. Microphone (native capture) — Calliope DSP

### What we know (evidence)
- Playback works via TAS2562 / AABox / UAIF0.
- Capture path was fully investigated: WDMA, SPUM and Calliope were identified.
- The native mic requires the **Calliope DSP firmware** (`calliope_sram.bin`,
  `calliope_dram.bin`, `calliope_iva.bin`), which is present but the DSP channel
  cannot be initialized on mainline.
- Bare-metal capture attempts were exhausted and closed.

### What is missing
- The Calliope firmware *format/loader path* expected by the mainline audio chain,
  or a mainline driver for the DSP (equivalent of the downstream `_calliope_` driver).
- Possibly a correct `UAIF` capture DAI link in the DTS (currently only playback
  UAIF0 is wired).

### Recommended steps
1. From the 4.14 tree, extract the Calliope DSP driver and its firmware loader:
   ```bash
   grep -ril calliope /home/fabio/gta4xl-4.14/sound /home/fabio/gta4xl-4.14/drivers
   ```
2. Identify the exact firmware files and versions the downstream driver expects;
   compare with the `calliope_*.bin` we have (hexdump the header).
3. Add a capture DAI link in `exynos9610-gta4xl-peripherals.dts` (ABOX ↔ UAIF1
   for the headset mic, per the `Headset: MIC hw_params` logs seen at boot).
4. Port the DSP init sequenced via ACPM.
5. Verify: `arecord -l`, `arecord -D hw:0,0 -f S16_LE -r 48000 /tmp/test.wav`.

### Risk / effort
High. This is the hardest item: DSP firmware is a black box. Likely out of reach
without the exact downstream driver port.

---

## 3. GPU — full acceleration (encoding / Metal / video)

### What we know (evidence)
- Panfrost works: `Mali-G72 MC3 (Panfrost)`, DRI3, EGL 1.5, GLES 3.1.
- DPU zero-copy works technically (`DPP+0x40 = 0xd3a00000`, CMA buffer with real pixels).
- Yet YouTube/Chromium remain not smooth, and `PageFlip` is disabled in Xorg.
- CPU/GPU clocks are low (schedutil, GPU devfreq ~260 MHz).
- MFC (video decode/encode) has incompatible firmware (`ip_ver 0x1202`, MFC v12.02).

### What is missing / how to improve
1. **PageFlip**: test `Option "PageFlip" "true"` in Xorg after zero-copy (never retested).
2. **Clock boosting**: verify ACPM DVFS; test with `performance` governor and
   force GPU to a higher devfreq; measure FPS with `glxgears`/`perf`.
3. **Video decode (MFC)**: need a compatible `s5p-mfc-v12.fw` firmware, or port the
   downstream `exynos/mfc` driver (~1 MB / 58 files, userspace-incompatible — see
   `dev/gemini-mfc-fw.txt` for the full analysis). Node is currently removed from DTS.
4. **Video encode**: same MFC block provides encode; blocked by the same firmware.
5. **HakiOS/Metal (experimental, not integrated)**: an Exynos 9611 iOS port exists
   (`speedyg2200/hakios-device-a51`); its GLES-on-Mali path proves Mali can be
   driven outside Linux, but Metal is Adreno-only there. See AI_WORKFLOW.md.

### Recommended steps (ordered by effort)
1. Test PageFlip true + performance governor (quick win, no code).
2. Measure real FPS and `hw_params` during YouTube (audio also — see §4).
3. Investigate MFC v12 firmware availability; if found, re-add the DTS node and
   test with `v4l2-ctl`/`gst-launch-1.0`.
4. Only as a last resort: evaluate the downstream MFC port.

### Risk / effort
Low for 1–2, high for 3–4.

---

## 4. Audio — playback already works; polish and verification

### What we know (evidence)
- Stereo playback via TAS2562 / AABox / UAIF0 is **working**.
- User reported audio sounding "2×" on YouTube — **never measured**.
- Headphone jack uses UAIF0 branch with `HEADPHONE Switch` and `jd-src=<1>` —
  never physically tested with headphones.

### What is missing / how to improve
1. **Measure, don't guess**: during YouTube playback run
   `cat /proc/asound/card0/pcm0p/sub0/hw_params` (rate, channels, format).
2. Check for a double path (ABOX + TAS2562 both active) with `pactl list sinks`
   or `amixer`.
3. Check for 44.1→48 kHz resampling in PipeWire/PulseAudio.
4. **Headphone jack**: perform the physical test with headphones; if the switch
   does not flip, inspect the jack GPIO/`jd-src` handling in the DTS.

### Risk / effort
Low. This is verification, not new driver work.

---

## 5. Priority summary

| Item | Effort | Priority | Blocker |
|---|---|---|---|
| Audio measurement + headphone test | Low | High | none (just test) |
| GPU PageFlip + clocks | Low | High | none (just test/config) |
| Bluetooth (`scsc_bt`) | Medium | Medium | driver port from 4.14 |
| MFC decode/encode | High | Low | firmware/driver |
| Native mic (Calliope) | High | Low | DSP firmware/loader |

## 6. Source base and rewrite scope (what to take from where)

The reference downstream tree is the **Samsung 4.14 kernel** (`gta4xl-4.14`),
still present on the author's WSL at `/home/fabio/gta4xl-4.14/`. The target is
**mainline 7.3** (this repository's `sources/linux-7.3`). Nothing from 4.14 can be
copied verbatim: the kernel APIs changed too much. Use it as a **map of what to
reimplement**, not as code to drop in.

### 6.1 Bluetooth — `scsc_bt`
**Source base (4.14):**
```
drivers/misc/samsung/scsc_bt/
  scsc_bt_module.c, scsc_bluez.c, scsc_bt_hci.h,
  scsc_bt_priv.h, scsc_shm.c/h, scsc_bt_qos.c, scsc_ant.c
include/scsc/scsc_mx.h, scsc_mifram.h
```
**What already exists on 7.3:** the working `scsc_wlbt` port (this repo,
`patches/upstream-wifi/`) — it already implements the shared MX/Shared-Memory
transport that BT also uses. **Reuse that, do not port the whole scsc stack.**

**Rewrite from scratch:**
- The BlueZ glue: 4.14 `scsc_bluez.c` uses the old `hci_alloc_dev()` / `hci_register_dev()`
  flow and old `struct hci_dev` fields. On 7.3 use `hci_alloc_dev()` with the current
  `hci_dev_ops` / `hci_uart` style and the modern `bt_skb`/`hci_recv_frame` API.
- The module init/power sequencing: replace 4.14 `scsc_bt_module.c` with a 7.3
  platform-driver probe that shares the wlbt power/reset GPIO and ACPM clock.
- Remove the 4.14 vendor QOS/ANT extras (`scsc_bt_qos.c`, `scsc_ant.c`) — keep the
  minimal HCI path first.

**Keep/adapt:** `scsc_shm.c/h` (shared-memory ring format) and the `scsc_mx.h`
message IDs — these are hardware protocol, not kernel API.

### 6.2 Microphone — Calliope DSP
**Source base (4.14):**
```
sound/soc/samsung/abox/          (ABOX DMA / UAIF capture paths)
sound/soc/samsung/exynos9610-rt5665.c  (codec DAI links — note the rt5665)
sound/soc/samsung/idma.c / idma.h      (IDMA capture)
```
Note: there is no file literally named `calliope` on 4.14 — the DSP firmware is
`calliope_*.bin` in `/lib/firmware`, driven through the ABOX/IPC path. Search the
downstream tree for the IPC command constants instead.

**Rewrite from scratch:**
- The ABOX IPC/DMA capture DAI link on 7.3: 4.14 uses the vendor `abox_` API;
  mainline has only the playback UAIF0 link. Add a capture link (headset mic →
  UAIF1 → ABOX → IDMA) in `exynos9610-gta4xl-peripherals.dts`.
- The DSP firmware loader sequence: reimplement the ACPM/Calliope boot commands
  with 7.3 firmware loader (`request_firmware` + `devm_`, not the 4.14 custom loader).

**Keep/adapt:** the `calliope_*.bin` firmware blobs themselves (already in the
sterile ROM's `/lib/firmware`) and the register offsets from `HARDWARE.md`.

### 6.3 MFC (decode + encode)
**Source base (4.14):**
```
drivers/media/platform/s5p-mfc/   (~58 files)
  s5p_mfc.c, s5p_mfc_dec.c, s5p_mfc_enc.c,
  s5p_mfc_opr_v6.c/h, s5p_mfc_cmd_v6.c/h,
  regs-mfc-v8.h (v12 register map lives here in the vendor tree)
```
**What already exists on 7.3:** `drivers/media/platform/samsung/s5p-mfc` mainline
driver — it probes (`ip_ver 0x1202`) but its firmware (`s5p-mfc-v10.fw`) is
incompatible. Full analysis in the author's `dev/gemini-mfc-fw.txt`.

**Rewrite from scratch / decision:**
- **Option A (preferred if firmware is found):** keep the mainline driver, obtain a
  compatible `s5p-mfc-v12.fw`, re-add the DTS node (the MFC node removal is
  re-applied by `scripts/reapply-kernel-patches.sh` — disable that for the test).
  No driver rewrite needed.
- **Option B (downstream port):** port only the v12 register ops from
  `s5p_mfc_opr_v6.c` + `regs-mfc-v8.h` into the mainline driver's `s5p_mfc_hw_ops`.
  Do **not** port the whole 58-file downstream driver: it is userspace-incompatible
  with mainline V4L2 (different ioctl/control ABI). Rewrite the ops layer, not the
  V4L2 layer.

### 6.4 WiFi (reference only — already working)
`drivers/misc/samsung/scsc/scsc_wifilogger_*`, `mx140_*.c` in 4.14. The 7.3 port in
`patches/upstream-wifi/` is the working reference for the shared transport; use it
as the model for the BT glue.

### 6.5 Practical extraction commands
```bash
# From the downstream tree on WSL:
find /home/fabio/gta4xl-4.14 -iname '*scsc*'
grep -ril calliope /home/fabio/gta4xl-4.14/sound /home/fabio/gta4xl-4.14/drivers
ls /home/fabio/gta4xl-4.14/drivers/media/platform/s5p-mfc/
```
Copy the **files** into a scratch dir outside this repo, read them, and write the
7.3 equivalent here as a new patch in `patches/upstream/`. Do not commit raw
downstream code (GPL attribution aside, it will not compile).

---

## 7. Implementation-level detail (for humans and AI assistants)

This section is intentionally specific: function names, kernel structs and the
4.14 → 7.3 API changes. An AI assistant should be able to start coding from this
without re-deriving the context. **Always verify against the actual 4.14 source
files before writing a patch** — line numbers and field names below are from the
field notes, not guaranteed to match your tree exactly.

### 8.1 Bluetooth — exact API mapping

**4.14 (`scsc_bluez.c`) — old API used:**
- `struct hci_dev *hdev = hci_alloc_dev();`
- `hdev->type = HCI_USB;` / `hdev->driver_name = "scsc_bt";`
- `hdev->open`, `hdev->close`, `hdev->flush`, `hdev->send`, `hdev->recv` (direct
  function-pointer fields on `struct hci_dev`).
- `hci_register_dev(hdev)` / `hci_unregister_dev(hdev)`.
- `hci_recv_frame(hdev, skb)` to inject RX packets.

**7.3 — what changed:**
- The direct `hdev->open/close/send/recv` fields are gone. Use the `hci_uart`
  framework: implement `struct hci_uart_proto` with `.open`, `.close`, `.recv`,
  `.send_frame`, `.flush`, and register with `hci_uart_register_proto()`.
  Files: `drivers/bluetooth/hci_uart.h`, `hci_ldisc.c`.
- Alternatively, for a pure virtual HCI device, use `hci_alloc_dev()` +
  `hci_register_dev()` but set ops through `hdev->ops`-equivalent callbacks and
  the modern `bt_skb_alloc()` / `hci_recv_frame()` (still present) — check
  `include/net/bluetooth/hci_core.h` in the 7.3 tree for the exact current fields.
- `struct hci_dev` fields like `driver_name`, `bus` are set via the `hci_uart`
  `.proto` struct, not by hand.
- Power/reset: 4.14 `scsc_bt_module.c` does raw `gpio_request` + `msleep` and
  `clk_prepare_enable` on vendor clocks. On 7.3 use `devm_gpiod_get()`,
  `gpiod_set_value_cansleep()`, and the ACPM clock consumer already used by
  `scsc_wlbt` (reuse its `clk` handle from the shared provider).
- Shared memory: `scsc_shm.c/h` uses `scsc_mifram` (physical ring buffers). Keep
  the ring format and the message IDs from `include/scsc/scsc_mx.h`, but replace
  any `ioremap`/`dma_alloc_coherent` calls with `devm_of_iomap()` /
  `dmam_alloc_coherent()` where possible.

**Acceptance test:**
```bash
hciconfig -a              # hci0 must appear
bluetoothctl power on
bluetoothctl show
bluetoothctl scan on      # must discover devices
```

### 8.2 Microphone — exact audio chain

**4.14 audio files (downstream):**
- `sound/soc/samsung/abox/` — ABOX DMA / UAIF.
- `sound/soc/samsung/exynos9610-rt5665.c` — codec DAI links (the actual codec is
  **rt5665**, not rt5765 — the boot log prints `rt5765-aif1_1`, verify both).
- `sound/soc/samsung/idma.c/h` — IDMA capture.

**What to search in the 4.14 tree:**
```bash
grep -rn "MIC\|CAPTURE\|calliope" /home/fabio/gta4xl-4.14/sound/soc/samsung/abox/ | head -40
grep -rn "calliope\|AUDIO_SLSI" /home/fabio/gta4xl-4.14/drivers/ | head -40
```

**7.3 side:**
- Mainline ASoC uses `snd_soc_dai_link` with `struct snd_soc_ops` (`.hw_params`,
  `.startup`, `.shutdown`). The 4.14 vendor ABOX code uses the old
  `samsung_asoc_dma`/`s3c_dma` helpers — do not port them.
- Add a **capture-only DAI link** in the machine driver: CPU DAI = ABOX UAIF1,
  codec DAI = rt5665 AIF1 (capture), platform = the existing mainline ABOX/IDMA
  PCM. The existing playback link is UAIF0 → TAS2562; keep it untouched.
- Firmware: `calliope_sram.bin`, `calliope_dram.bin`, `calliope_iva.bin` are in
  `/lib/firmware` of the sterile ROM. Load with `request_firmware()` from the
  machine driver probe, then send the DSP boot command sequence recovered from
  the 4.14 IPC constants (find them with the grep above).
- DTS: add the capture link under the ABOX node in
  `exynos9610-gta4xl-peripherals.dts` (already has the playback UAIF0 branch with
  `HEADPHONE Switch` and `jd-src=<1>`).

**Acceptance test:**
```bash
arecord -l                                    # capture device listed
arecord -D hw:0,1 -f S16_LE -r 48000 -d 5 /tmp/mic.wav
```

### 8.3 MFC — minimal ops-port path

**4.14 files:** `drivers/media/platform/s5p-mfc/s5p_mfc_opr_v6.c`,
`s5p_mfc_opr_v6.h`, `regs-mfc-v8.h`, `s5p_mfc_cmd_v6.c`.

**7.3 side:** `drivers/media/platform/samsung/s5p-mfc/s5p_mfc_hw_ops.c` (or the
`ops_v12` file — verify). The driver already probes with `ip_ver 0x1202` but its
firmware file is `s5p-mfc-v10.fw`.

**Steps:**
1. Search for an `s5p-mfc-v12.fw` in linux-firmware or the 4.14 tree's `revision.txt`.
2. If found: re-add the DTS node removed by `scripts/reapply-kernel-patches.sh`,
   install the firmware, test decode/encode with `gst-launch-1.0`.
3. If not found: port ONLY the v12 register programming from
   `s5p_mfc_opr_v6.c`/`regs-mfc-v8.h` into the mainline `s5p_mfc_hw_ops` struct
   (`.mfc_init_hw`, `.mfc_enc/dec_cmd`, `.mfc_get_int_reason`, etc.).
   Do **not** copy the 4.14 V4L2 ioctl layer — its control ABI differs from mainline.
4. Full analysis: author's `dev/gemini-mfc-fw.txt` (summarize, don't paste raw logs).

**Acceptance test:**
```bash
v4l2-ctl --list-formats-out -d /dev/video0
gst-launch-1.0 filesrc location=test.mp4 ! decodebin ! fakesink
```

### 8.4 Audio playback — verification only (already working)

**No code needed.** During YouTube playback, run:
```bash
cat /proc/asound/card0/pcm0p/sub0/hw_params   # expect 48000 Hz, 2ch, S16_LE/S32_LE
pactl list sinks | grep -A5 'Name:'
```
If "2×" is perceived, check for two active outputs (ABOX + TAS2562) or
44.1→48 kHz resampling. Headphone jack: physically test; if the switch does not
flip, inspect `HEADPHONE Switch` / `jd-src=<1>` in the DTS.

---

## 8. Where the source data lives

- Downstream 4.14 kernel (for driver extraction): `/home/fabio/gta4xl-4.14/` on WSL.
- Mainline 7.3 tree and patches: this repository (`patches/`, `docs/HARDWARE.md`).
- Full Gemini analyses: original `dev/gemini-*.txt` files in the author's project
  tree (not in this repo — they contain field-specific notes; summarize, do not
  paste raw personal logs).
