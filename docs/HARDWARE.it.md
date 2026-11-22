# HARDWARE.it.md — Mappa hardware (Italiano)

Versione primaria: [HARDWARE.md](HARDWARE.md). Solo dati hardware, nessun dato personale.

## SoC
Exynos 9611 (SM-P610), 4× A73 + 4× A53 ARMv8.0 (pagine 4 KB), GPU Mali-G72 MP3 (Panfrost).

## Indirizzi MMIO validati
| Blocco | Indirizzo |
|---|---|
| DPU/DECON | `0x14881000`, `0x14891000` |
| DPP base | `DPP+0x40 = 0xd3a00000` |
| HSI2C3 (touch) | `0x11d10000` |
| ABOX (audio) | `0x14a50000` |
| PS_HOLD | `0x330c` |
| MFC | `0x12c30000` (disabilitato) |

## Display
DSI 1200×2000 @ 67.051 Hz, Xorg `modesetting` + `DRI 3`, `PageFlip false`.

## Firmware
`mx140*` (WiFi), `AP_*_AUDIO_SLSI` (audio), `calliope_*` (DSP, mic non funzionante), plugin ACPM (DVFS).

## Note
WiFi funzionante (`scsc_wlbt`); Bluetooth richiede `scsc_bt`; MFC ha firmware incompatibile → nodo rimosso dal DTS.
