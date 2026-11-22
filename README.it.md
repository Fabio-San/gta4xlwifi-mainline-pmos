# gta4xlwifi-mainline-pmos (Italiano)

Mainline Linux 7.3 + postmarketOS (XFCE) per **Samsung Galaxy Tab S6 Lite LTE (SM-P610 / gta4xlwifi, Exynos 9611)**.

Questo repository contiene sorgenti kernel, patch, script di build/flash sicuri, un builder per una **ROM sterile avviabile** (senza dati personali) e documentazione completa.

> **Stato**: configurazione sperimentale, non una ROM di produzione. Kernel e rootfs qui descritti sono stati verificati sul campo su un SM-P610; la ROM *sterile* è preparata da questa configurazione ma **non è stata testata come pacchetto finale** (vedi [Known issues](docs/KNOWN_ISSUES.md)). Leggere sempre [FLASH.md](docs/FLASH.md) prima di toccare il dispositivo.

Versione primaria (inglese): [README.md](README.md)

---

## Cosa funziona (verificato)

| Funzione | Stato | Note |
|---|---|---|
| Boot mainline 7.3 via uniLoader | ✅ | senza flashare bootloader/vbmeta |
| UI XFCE (modesetting + Panfrost) | ✅ | DRI3, DPU zero-copy |
| WiFi | ✅ | driver `scsc_wlbt`, firmware mx140 |
| Audio stereo (TAS2562) | ✅ | AABox/UAIF0 |
| Jack cuffie | ⚠️ | branch UAIF0, mai testato fisicamente |
| Rete / SSH | ✅ | **disattivato di default**, attivabile |
| Poweroff/riavvio | ✅ | PS_HOLD |
| Volume/orologio persistenti | ✅ | |
| Touchscreen | ✅ | Himax HX83102E via SPI |
| Batteria/ricarica | ✅ | |
| Fluidità video | ⚠️ | Panfrost + zero-copy OK, ma YouTube/Chromium poco fluidi |
| Mic nativo | ❌ | richiede firmware Calliope/DSP |
| MFC (decode HW) | ❌ | firmware incompatibile, disabilitato nel DTS |
| Bluetooth | ❌ | serve driver `scsc_bt` |

---

## Quick start

```bash
git clone https://github.com/Fabio-San/gta4xlwifi-mainline-pmos.git
cd gta4xlwifi-mainline-pmos && git checkout pmos
bash scripts/setup-build-env.sh
bash scripts/build-upstream.sh
```

Flash da Windows in Lineage Recovery:
```powershell
.\scripts\flash-boot-adb.ps1 -Image .\artifacts\boot.img -Serial <SERIAL>
```

ROM sterile: `bash scripts/make-sterile-rom.sh`

ROM precompilata: [Release v7.3-pmos-20261122](https://github.com/Fabio-San/gta4xlwifi-mainline-pmos/releases/tag/v7.3-pmos-20261122) — `gta4xlwifi-pmos-7.3-20261122.zip`, SHA256 `f1ed8fb1e823bf52646d033e2a6c989b24b30d5505b3b93ef8d199c245f8e27c`. Verificare il checksum prima di flashare. **Build NON testata come pacchetto finale**: se la provi, segui [TESTING.it.md](docs/TESTING.it.md) e riporta i risultati (soprattutto gli errori) in una Issue GitHub con tag `rom-test`.

---

## ROM sterile — account e SSH

| Elemento | Valore |
|---|---|
| Utente predefinito | `gta4xlwifi` |
| Password predefinita | `147147` |
| Tastiera virtuale | `onboard`, avvio automatico, tasti grandi |
| SSH | **NON avviato** all'avvio |
| Attivazione SSH | icona "SSH" nel menu XFCE oppure `sudo rc-service sshd start` |

> **⚠️ CAMBIA SUBITO LA PASSWORD** dopo il primo accesso (`passwd`).

---

## Sicurezza

- **NON flashare MAI `bootloader`** (né `vbmeta`).
- Usa sempre gli script ADB da recovery, non Odin per `boot`.
- **Fai sempre il backup** di boot/dtbo/recovery/vbmeta (lo script lo fa).
- Nessun dato personale nel repo. La ROM sterile rigenera `machine-id` e chiavi SSH.

---

## Crediti

Questo lavoro è il risultato della collaborazione tra una persona e diversi assistenti IA:

- **Fabio-San** — idea, direzione, hardware, tempo, energie, test sul campo e decisioni.
- **Hy4 flash Free (OpenCode)** — il grosso del lavoro ingegneristico: debug kernel, DTS, indagine display/audio/MFC, initramfs e chroot, builder ROM sterile, documentazione e repo.
- **Gemini 4 Hydrogen** — analisi approfondite su mount propagation, GSettings/systemd, firmware MFC e registri hardware.
- **ChatGPT Luna 6** e **Antigravity** — ulteriori ragionamenti e verifiche incrociate.

Grazie anche alle community **postmarketOS** e **mainline Linux**, agli autori delle patch in `patches/upstream/` e alla community **gta4xl**.

Vedi [docs/AI_WORKFLOW.it.md](docs/AI_WORKFLOW.it.md) per come continuare a lavorare con le IA.

## Licenza

Codice e documentazione: **MIT**. Kernel e patch: **GPL-2.0**. Binari in `tools/`: licenze rispettive. Vedi [NOTICE.md](NOTICE.md).
