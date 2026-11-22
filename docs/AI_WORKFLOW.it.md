# AI_WORKFLOW.it.md — Lavorare con le IA su questo port (Italiano)

Versione primaria: [AI_WORKFLOW.md](AI_WORKFLOW.md)

Questo port è nato dalla collaborazione tra Fabio-San e diversi assistenti IA
(Hy4 flash Free / OpenCode, Gemini 4 Hydrogen, ChatGPT Luna 6, Antigravity).

## 1. L'umano dà la direzione, l'IA fa il lavoro pesante
- **Umano**: decide cosa provare, possiede l'hardware, esegue flash/reboot, riporta cosa appare a schermo, decide il rischio.
- **IA**: indaga il codice, legge i log, scrive script, ragiona sulle cause, produce documentazione.

L'IA non deve mai flashare nulla senza conferma esplicita. Ogni flash è stato preceduto da un backup verificato.

## 2. Il prompt che ha funzionato meglio con Gemini
```
Dai una risposta completa dopo analisi e ragionamenti profondi e sensati, senza inventare nulla
```
Chiedere risposte basate su evidenze, etichettare le speculazioni, e dire "non lo so" quando i log non bastano.

## 3. Dare sempre all'IA le evidenze reali
Includere: testo esatto dell'errore (dmesg/journal/pstore/schermo), SHA256 del boot.img usato, `uname -r`, `/etc/os-release`, cosa è già stato provato e cosa è cambiato.

## 4. Verificare le affermazioni dell'IA con fonti primarie
Se l'IA cita un repo/file/indirizzo/commit, **aprirlo**. Se non si apre, trattarlo come non verificato. (Abbiamo verificato così i repo HakiOS reali tramite GitHub API.)

## 5. Una sola fonte di verità
Questo repo è la fonte di verità per config, patch e docs. Non lasciare script "finali" solo in una chat: committarli qui. Aggiornare `WORKLOG.md`.

## 6. Regole di sicurezza per flash con IA
1. Mai flashare senza conferma umana esplicita.
2. Backup di boot, dtbo, recovery, vbmeta prima di tutto.
3. **Mai flashare `bootloader` o `vbmeta`**.
4. Dopo ogni flash, verificare rileggendo la partizione e confrontando lo SHA256.
5. Se un boot fallisce, ripristinare l'immagine buona prima di continuare.

## 7. Proteggere i dati personali
Non incollare mai password WiFi, seriali, MAC, IP, chiavi SSH o file personali in prompt o repo. Usare placeholder (`<SERIAL>`, `<IP>`, `<SSID>`). Il builder ROM sterile ha un controllo automatico dei pattern sensibili.

## 8. Ruoli osservati
| Assistente | Ha funzionato meglio per |
|---|---|
| Hy4 flash Free (OpenCode) | Codice, script, debug iterativo, repo/docs |
| Gemini 4 Hydrogen | Ragionamento kernel/VFS, firmware, verifiche |
| ChatGPT Luna 6 | Ragionamenti alternativi, seconde opinioni |
| Antigravity | Analisi e validazione aggiuntive |

Per i problemi difficili usare **due modelli**: chiedere a uno la causa, all'altro di criticarla.

## 9. Regola finale
L'IA è un collega velocissimo e sicuro di sé, ma a volte inventa. Log, hash e fonti primarie vincono sempre su qualsiasi spiegazione.
