# WORKLOG.md — Porting chronology

Summary of the work done on the SM-P610 (gta4xlwifi) with mainline Linux 7.3.
Context for anyone continuing the port.

> Italian: [WORKLOG.it.md](WORKLOG.it.md)

## Phase 1 — Boot and display
- Mainline 7.3 boot via uniLoader (init embedded in the kernel, not the outer ramdisk).
- KMS fix: `.fb_create = drm_gem_fb_create_with_dirty` → XFCE visible with modesetting.
- DPU driver (`exynos9610_drm.c`) with CMA/zero-copy: `DPP+0x40 = 0xd3a00000`.
- Xorg: `modesetting` + `DRI 3`, 1200×2000 @ 67Hz panel.

## Phase 2 — Audio
- Stereo TAS2562 via AABox/UAIF0 working.
- Headphone jack: UAIF0 branch, `HEADPHONE Switch`, `jd-src=<1>` (not physically tested).
- Native mic: investigation closed (requires Calliope/DSP firmware).

## Phase 3 — Power and peripherals
- Poweroff/reboot via PS_HOLD `0x330c`.
- Persistent volume and clock.
- WiFi via `scsc_wlbt` + mx140 firmware.
- Himax HX83102E touchscreen over SPI.

## Phase 4 — Experiments (not part of the stable ROM)
- **MFC**: probe OK but incompatible firmware → node removed from DTS.
- **Mobian/Debian forky**: systemd 262 in a nested chroot needs `mount --bind` + `--make-rshared` + GSettings schemas; Phosh was started but abandoned for extreme slowness (upower loop). pmOS/OpenRC remains the stable choice.
- **HakiOS/iOS**: evaluated as a future experiment (an Exynos 9611 port exists); not integrated.

## Phase 5 — Stabilization
- Full verified backup (`pmos-backup-20261121-2245.tar.gz`, SHA `cd989da6…`).
- Restored original pmos-init (SHA `2f87e1be…`) and verified boot (`d71a7d11…`).
- Sterile ROM and documentation prepared (this repository).

## Architectural decisions
- **OpenRC (pmOS) over systemd**: modern systemd needs namespaces/cgroups that the allnoconfig kernel does not expose well in a chroot; OpenRC is lighter and stable here.
- **Kernel from source with patches**: config comes from a reduced baseline; patches in `patches/upstream/` are required for display, GPU, clocks, power and WiFi.
- **Never flash bootloader/vbmeta**: all changes are confined to the `boot` partition.
