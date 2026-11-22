# STERILE-ROM.it.md — ROM sterile, account e SSH (Italiano)

Versione primaria: [STERILE-ROM.md](STERILE-ROM.md)

## Contenuto dello zip
`boot.img` (SHA `d71a7d11…`) + `rootfs.tar.gz` sterile + script flash + README + SHA256SUMS.

La rootfs è **ricostruita pulita**, non copiata da un backup personale.

### Incluso
Cartelle standard vuote (Desktop, Downloads, Music, Pictures, Templates, Videos), firmware hardware, moduli kernel, config XFCE base, `onboard` con tasti grandi, server SSH installato ma disattivato, utente predefinito.

### Indirizzamento di rete (DHCP, non statico)
- Il gadget RNDIS USB (`tools/setup-rndis.sh`) si limita a collegare il gadget USB: **non assegna alcun IP**. L'host/router collegato fornisce l'indirizzo via DHCP, quindi SSH e tethering USB prendono un indirizzo in base alla rete usata.
- Nessun IP statico, SSID/password WiFi salvati o indirizzo `192.168.x.x` sono presenti nella rootfs sterile: non c'è nessuna "rete di casa" hardcoded.

### Escluso
File utente, `.gnupg`, `.dbus`, credenziali WiFi, chiavi SSH, `machine-id`, log, seriali.

### Rigenerato al primo avvio
`/etc/machine-id`, chiavi host SSH.

## Account predefinito
Utente `gta4xlwifi`, password `147147` — **cambiarla subito** (`passwd`).

## SSH
Non avviato all'avvio. Attivazione:
- Terminale: `sudo rc-service sshd start` / `sudo rc-update add sshd default`
- GUI: icona "SSH" nel menu XFCE (finestra zenity)

## Tastiera virtuale
`onboard` auto-avviato con tasti grandi (`device/onboard.conf`).

## Build
```bash
bash scripts/make-sterile-rom.sh
```
Verifica automatica dei pattern sensibili prima di impacchettare.
