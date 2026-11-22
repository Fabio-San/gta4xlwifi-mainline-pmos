# WORKLOG.it.md — Cronologia del porting (Italiano)

Versione primaria: [WORKLOG.md](WORKLOG.md)

- **Fase 1 — Boot/display**: boot 7.3 via uniLoader, fix KMS (`drm_gem_fb_create_with_dirty`), DPU zero-copy, XFCE modesetting/DRI3.
- **Fase 2 — Audio**: stereo TAS2562 via AABox/UAIF0; jack cuffie (non testato); mic chiuso (serve Calliope).
- **Fase 3 — Potenza/periferiche**: PS_HOLD `0x330c`, volume/orologio persistenti, WiFi `scsc_wlbt`, touch Himax.
- **Fase 4 — Esperimenti**: MFC (firmware incompatibile, nodo rimosso); Mobian/systemd (abbandonato per lentezza); HakiOS/iOS (valutato, non integrato).
- **Fase 5 — Stabilizzazione**: backup verificato, ripristino pmos-init (`2f87e1be`), boot verificato (`d71a7d11`), ROM sterile e documentazione.

Decisioni: OpenRC invece di systemd; kernel con patch; mai flashare bootloader/vbmeta.
