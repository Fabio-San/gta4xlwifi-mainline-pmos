# ROADMAP.it.md — Piano d'azione per le funzionalità mancanti (Italiano)

Versione primaria: [ROADMAP.md](ROADMAP.md)

Raccoglie azioni, dati e riferimenti concreti per completare Bluetooth, microfono, GPU e audio, basati sulle evidenze raccolte sul campo.

## 1. Bluetooth — port del driver `scsc_bt`
- **Noto**: `scsc_wlbt` carica e il WiFi funziona; manca il client BT. Manca il driver `scsc_bt`, presente nel 4.14.
- **Manca**: `drivers/bluetooth/scsc_bt*`, firmware `bt_fw.bin`, nodo DTS, sequenza power/reset condivisa col WiFi.
- **Passi**: 1) trova `scsc_bt` in `/home/fabio/gta4xl-4.14/`; 2) confronta col `scsc_wlbt` già portato (`patches/upstream-wifi/`); 3) porta le API HCI 7.3; 4) aggiungi firmware e DTS; 5) verifica `hciconfig -a` / `bluetoothctl`.
- **Sforzo**: medio (trasporto già provato dal WiFi).
- **SCOPERTA IMPORTANTE**: esiste già un `scsc_bt.ko` precompilato in `sources/scsc-upstream/` (insieme a `scsc_wlan.ko`, `scsc_mx.ko`). Controllare `modinfo ...scsc_bt.ko` per il `vermagic` con `7.3.0-gta4xl-upstream`, poi provare `insmod` e `hciconfig -a` prima di portare il driver: potrebbe mancare solo firmware/DTS.

## 2. Microfono nativo — Calliope DSP
- **Noto**: playback OK; capture richiede DSP Calliope (`calliope_*.bin` presenti ma canale DSP non inizializzato). Tentativi bare-metal esauriti.
- **Manca**: driver/loader DSP mainline, link DAI di capture (forse UAIF1 per il mic cuffia).
- **Passi**: estrai driver Calliope dal 4.14 (`grep -ril calliope .../sound .../drivers`), confronta i firmware, aggiungi link DAI, porta sequenza ACPM, verifica `arecord`.
- **Sforzo**: alto — il firmware DSP è una scatola nera.

## 3. GPU — accelerazione completa (encoding/video)
- **Noto**: Panfrost + DPU zero-copy funzionanti; YouTube/Chromium poco fluidi; `PageFlip false`; clock bassi (GPU ~260 MHz); MFC `ip_ver 0x1202` con firmware incompatibile.
- **Passi (per sforzo)**: 1) prova `PageFlip true` + governor `performance`; 2) misura FPS e `hw_params`; 3) cerca firmware `s5p-mfc-v12.fw`; 4) solo in extremis porta il driver `exynos/mfc` downstream (~1 MB/58 file, userspace-incompatibile).
- **Sforzo**: basso per 1–2, alto per 3–4.

## 4. Audio — playback già OK, da verificare
- **Noto**: stereo TAS2562/AABox/UAIF0 funzionante. Audio "2×" su YouTube **non misurato**. Jack cuffie (UAIF0, `HEADPHONE Switch`, `jd-src=<1>`) mai testato fisicamente.
- **Passi**: misura `hw_params` durante riproduzione; controlla doppio path ABOX+TAS2562; verifica resampling 44.1→48 kHz; test fisico con cuffie.
- **Sforzo**: basso (solo verifica).

## 5. Priorità
| Voce | Sforzo | Priorità | Blocco |
|---|---|---|---|
| Misura audio + test cuffie | Basso | Alta | nessuno |
| GPU PageFlip + clock | Basso | Alta | nessuno |
| Bluetooth | Medio | Media | port driver 4.14 |
| MFC decode/encode | Alto | Bassa | firmware/driver |
| Mic Calliope | Alto | Bassa | DSP firmware |

## 6. Base sorgente e cosa riscrivere (da dove prendere cosa)

L'albero downstream di riferimento è il **kernel Samsung 4.14** (`gta4xl-4.14`, su WSL in `/home/fabio/gta4xl-4.14/`). Il target è il **mainline 7.3** (questo repo). Nulla del 4.14 si può copiare tale e quale: le API sono cambiate troppo. Usa il 4.14 come **mappa di cosa reimplementare**, non come codice da incollare.

### 6.1 Bluetooth — `scsc_bt`
**Base 4.14:** `drivers/misc/samsung/scsc_bt/` (scsc_bt_module.c, scsc_bluez.c, scsc_bt_hci.h, scsc_shm.c/h, scsc_bt_qos.c, scsc_ant.c), `include/scsc/scsc_mx.h`.
**Già su 7.3:** il port `scsc_wlbt` funzionante (`patches/upstream-wifi/`) — implementa già il trasporto MX/Shared-Memory condiviso. **Riutilizza quello, non portare tutto lo stack scsc.**
**Riscrivere da zero:** il glue BlueZ (4.14 usa vecchio `hci_register_dev`/`struct hci_dev`; su 7.3 usare API HCI moderne), l'init/power sequencing come platform-driver 7.3, e scartare QOS/ANT (tenere solo il percorso HCI minimo).
**Tenere/adattare:** `scsc_shm.c/h` e gli ID messaggio `scsc_mx.h` (sono protocollo hardware).

### 6.2 Microfono — Calliope DSP
**Base 4.14:** `sound/soc/samsung/abox/`, `exynos9610-rt5665.c`, `idma.c/h`. Non esiste un file chiamato `calliope`: il firmware `calliope_*.bin` è pilotato tramite ABOX/IPC — cercare le costanti IPC nel 4.14.
**Riscrivere da zero:** il link DAI di capture ABOX/IPC su 7.3 (aggiungere headset mic → UAIF1 → ABOX → IDMA nel DTS) e il sequenziatore firmware (usare `request_firmware`/`devm` di 7.3).
**Tenere:** i blob `calliope_*.bin` (già nella ROM sterile) e gli offset registro di `HARDWARE.md`.

### 6.3 MFC (decode + encode)
**Base 4.14:** `drivers/media/platform/s5p-mfc/` (~58 file: s5p_mfc.c, _dec.c, _enc.c, _opr_v6.c/h, _cmd_v6.c/h, regs-mfc-v8.h).
**Già su 7.3:** driver mainline che fa probe (`ip_ver 0x1202`) ma con firmware incompatibile.
**Opzioni:** A) preferita — trovare `s5p-mfc-v12.fw` e riaggiungere il nodo DTS (disabilitando `reapply-kernel-patches.sh`); B) portare solo le ops v12 (`s5p_mfc_opr_v6.c` + `regs-mfc-v8.h`) nella struct `s5p_mfc_hw_ops` del driver mainline — **non** portare tutto il driver downstream (ABI V4L2 incompatibile).

### 6.4 WiFi (referenza)
`drivers/misc/samsung/scsc/` e `mx140_*.c` nel 4.14. Il port 7.3 in `patches/upstream-wifi/` è il modello funzionante per il glue BT.

### 6.5 Comandi di estrazione
```bash
find /home/fabio/gta4xl-4.14 -iname '*scsc*'
grep -ril calliope /home/fabio/gta4xl-4.14/sound /home/fabio/gta4xl-4.14/drivers
ls /home/fabio/gta4xl-4.14/drivers/media/platform/s5p-mfc/
```
Copiare i file in una cartella temporanea fuori dal repo, leggerli, e scrivere l'equivalente 7.3 come nuova patch in `patches/upstream/`.

## 7. Dettagli a livello di implementazione (per umani e IA)

Questa sezione è volutamente specifica: nomi di funzioni, struct kernel e differenze API 4.14 → 7.3. Un'assistente IA dovrebbe poter iniziare a scrivere codice da qui. **Verificare sempre sui file 4.14 reali prima di scrivere una patch.**

### 7.1 Bluetooth — mapping API esatto
**4.14 (`scsc_bluez.c`)**: `hci_alloc_dev()`, campi diretti `hdev->open/close/flush/send/recv`, `hci_register_dev()`, `hci_recv_frame()`.
**7.3**: i campi diretti non esistono più. Usare il framework `hci_uart`: implementare `struct hci_uart_proto` con `.open/.close/.recv/.send_frame/.flush` e registrare con `hci_uart_register_proto()` (file `drivers/bluetooth/hci_uart.h`, `hci_ldisc.c`). In alternativa device HCI virtuale con callback moderni e `bt_skb_alloc()` / `hci_recv_frame()` — verificare `include/net/bluetooth/hci_core.h`.
**Power/reset**: 4.14 usa `gpio_request`/`msleep`/clk vendor; su 7.3 usare `devm_gpiod_get()`, `gpiod_set_value_cansleep()`, e l'handle ACPM condiviso con `scsc_wlbt`.
**Shared memory**: `scsc_shm.c/h` — tenere formato ring e ID messaggio di `scsc_mx.h`, sostituire `ioremap`/`dma_alloc_coherent` con `devm_of_iomap()`/`dmam_alloc_coherent()`.
**Test**: `hciconfig -a`, `bluetoothctl power on`, `bluetoothctl scan on`.

### 7.2 Microfono — catena audio esatta
**File 4.14**: `sound/soc/samsung/abox/`, `exynos9610-rt5665.c` (il codec è **rt5665**, il log stampa `rt5765-aif1_1` — verificare entrambi), `idma.c/h`.
**Ricerca**: `grep -rn "MIC\|CAPTURE\|calliope" .../sound/soc/samsung/abox/` e `grep -rn "calliope\|AUDIO_SLSI" .../drivers/`.
**7.3**: ASoC mainline usa `snd_soc_dai_link` con `struct snd_soc_ops` (`.hw_params`, `.startup`, `.shutdown`). Non portare gli helper vendor `samsung_asoc_dma`/`s3c_dma`. Aggiungere un **DAI link di sola capture**: CPU DAI = ABOX UAIF1, codec DAI = rt5665 AIF1 (capture), platform = IDMA mainline. Il link playback UAIF0 → TAS2562 resta intatto.
**Firmware**: `calliope_sram/dram/iva.bin` già in `/lib/firmware`; caricare con `request_firmware()` e inviare la sequenza IPC recuperata dalle costanti 4.14.
**DTS**: aggiungere il link capture sotto il nodo ABOX in `exynos9610-gta4xl-peripherals.dts`.
**Test**: `arecord -l`, `arecord -D hw:0,1 -f S16_LE -r 48000 -d 5 /tmp/mic.wav`.

### 7.3 MFC — via minima di port
**File 4.14**: `s5p_mfc_opr_v6.c/h`, `regs-mfc-v8.h`, `s5p_mfc_cmd_v6.c`.
**7.3**: `drivers/media/platform/samsung/s5p-mfc/`, driver che fa probe con `ip_ver 0x1202` ma firmware `s5p-mfc-v10.fw`.
**Passi**: 1) cercare `s5p-mfc-v12.fw`; 2) se trovato, riaggiungere il nodo DTS rimosso da `reapply-kernel-patches.sh` e testare; 3) altrimenti portare SOLO la programmazione registri v12 nella struct `s5p_mfc_hw_ops` (`.mfc_init_hw`, `.mfc_enc/dec_cmd`, `.mfc_get_int_reason`). **Non** copiare il layer V4L2 4.14 (ABI ioctl diverso).
**Test**: `v4l2-ctl --list-formats-out -d /dev/video0`, `gst-launch-1.0 ...`.

### 7.4 Audio playback — solo verifica (già funzionante)
Nessun codice. Durante YouTube: `cat /proc/asound/card0/pcm0p/sub0/hw_params`, `pactl list sinks`. Se si percepisce "2×", controllare doppio output ABOX+TAS2562 o resampling 44.1→48 kHz. Jack cuffie: test fisico, poi controllare `HEADPHONE Switch`/`jd-src=<1>` nel DTS.

## 8. Dove stanno i dati
Kernel 4.14 su WSL, albero 7.3 e patch in questo repo, analisi Gemini nel progetto originale (non in questa repo: riassumere, non incollare log grezzi).
