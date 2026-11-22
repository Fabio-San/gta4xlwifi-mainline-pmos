# FLASH.it.md — Flash sicuro e rollback (Italiano)

Versione primaria: [FLASH.md](FLASH.md)

## Regole d'oro
1. **NON flashare MAI `bootloader`** (né `vbmeta`).
2. Fai sempre il backup di `boot`, `dtbo`, `recovery`, `vbmeta`.
3. Usa lo script Windows `scripts/flash-boot-adb.ps1` (WSL adb non vede il dispositivo).
4. Non usare Odin per `boot`.

## Preparazione
Tablet in Lineage Recovery, PC Windows con adb, batteria > 50%.
```powershell
adb devices -l
```

## Flash (con backup automatico)
```powershell
.\scripts\flash-boot-adb.ps1 -Image .\artifacts\boot.img -Serial <SERIAL>
```
Lo script: backup → push → dd → **rilettura e confronto byte-per-byte**.
Se vedi `verifica OK: partizione boot identica all'immagine`, è andato tutto bene.

## Verifica
```powershell
adb reboot
# via SSH: ssh gta4xlwifi@<TABLET_IP> (password 147147)
uname -r   # 7.3.0-gta4xl-upstream
```

## Rollback
Riavvia in recovery e flasha il backup:
```powershell
.\scripts\flash-boot-adb.ps1 -Image .\backups\live\boot-<timestamp>.img -Serial <SERIAL>
```

## Partizioni
`boot` = `/dev/sda12` (qui si flasha), `rootfs` = `/dev/sda32`. `dtbo`/`recovery`/`vbmeta`: **non toccare**.
