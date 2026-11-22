# TESTING.it.md — Test della ROM sterile (build NON testata)

> **Questa ROM NON è stata testata come pacchetto finale.** Kernel e rootfs sono stati verificati separatamente su un SM-P610, ma lo zip sterile non è mai stato flashato/bootstrappato interamente dall'autore. **Flashare a proprio rischio, sempre con backup.**

Versione primaria: [TESTING.md](TESTING.md)

## 1. Prima di flashare (obbligatorio)
1. Backup di `boot`, `dtbo`, `recovery`, `vbmeta` (vedi FLASH.md).
2. Verifica checksum: `sha256sum gta4xlwifi-pmos-7.3-20261122.zip` → `f1ed8fb1...`
3. Batteria > 50%, tablet in Lineage Recovery.

## 2. Cosa testare (in ordine)
| # | Test | Atteso | OK? |
|---|---|---|---|
| 1 | Flash boot.img + estrazione rootfs, reboot | Appare XFCE | ☐ |
| 2 | Script primo avvio | utente `gta4xlwifi` creato, machine-id/chiavi SSH rigenerate | ☐ |
| 3 | Login | `gta4xlwifi` / `147147` funziona | ☐ |
| 4 | Tastiera onboard | compare, tasti grandi, usabile | ☐ |
| 5 | WiFi | si connette (inserire le proprie credenziali) | ☐ |
| 6 | SSH spento di default | porta 22 chiusa finché non attivato | ☐ |
| 7 | SSH via icona GUI | app "SSH Server" nel menu XFCE lo avvia | ☐ |
| 8 | SSH via terminale | `sudo rc-service sshd start` funziona | ☐ |
| 9 | Audio | altoparlanti stereo | ☐ |
| 10 | Display/touch | 1200x2000, touch reattivo | ☐ |
| 11 | Poweroff/reboot | funziona | ☐ |
| 12 | Cambio password | `passwd` funziona | ☐ |

## 3. Cosa riportare (tutto)
Apri una **Issue** GitHub con tag `rom-test` e includi:
1. Risultati della tabella.
2. **Messaggi di errore esatti** (copiati alla lettera).
3. SHA256 del boot.img flashato.
4. Dove si è fermato: recovery? boot logo? login? XFCE?
5. Log come allegati: `dmesg > dmesg.txt`, `cat /etc/os-release`.
6. Dispositivo (SM-P610/P615) e ROM precedente.

> **Non includere** dati personali: seriali, MAC, IP, password WiFi, chiavi.

## 4. Limitazioni note (non segnalarle come bug)
Nessun mic nativo, nessun MFC decode/encode, nessun Bluetooth, GPU non fluida, jack cuffie non testato — vedi KNOWN_ISSUES.md.

## 5. Rollback
Se qualcosa fallisce, riflasha il boot.img originale e ripristina i dati dal tuo backup. Vedi FLASH.md.
