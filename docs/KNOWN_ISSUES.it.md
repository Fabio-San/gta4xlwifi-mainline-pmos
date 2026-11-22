# KNOWN_ISSUES.it.md — Stato funzionale e miglioramenti (Italiano)

Versione primaria: [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

## Matrice
| Funzione | Stato | Possibile soluzione |
|---|---|---|
| Boot 7.3, display, touch, WiFi, audio stereo, poweroff, batteria | ✅ | — |
| Jack cuffie | ⚠️ | test fisico con cuffie |
| Fluidità video | ⚠️ | provare `PageFlip true`, `mpv --vo=gpu`, misurare FPS |
| Audio "2×" | ⚠️ | misurare `hw_params` durante riproduzione |
| Mic nativo | ❌ | serve firmware Calliope/DSP |
| MFC decode/encode | ❌ | serve firmware v12 compatibile o port driver downstream |
| Bluetooth | ❌ | portare driver `scsc_bt` dal 4.14 |
| Clock CPU/GPU bassi | ⚠️ | verificare DVFS ACPM, provare governor `performance` |

## Dettagli
- **MFC**: `ip_ver 0x1202`, firmware Lineage incompatibile → loop di timeout; nodo rimosso dal DTS.
- **Audio**: verificare doppio path ABOX+TAS2562 e resampling 44.1→48 kHz.
- **GPU**: zero-copy tecnicamente attivo ma non percepito; PageFlip mai ritestato.
- **Mic**: investimento chiuso, richiede DSP.

Cronologia dettagliata: `WORKLOG.md`.
