# FLASH.md — Safe flashing and rollback

> **READ FULLY BEFORE STARTING.**

> Italian: [FLASH.it.md](FLASH.it.md)

## Golden rules

1. **NEVER flash the `bootloader` partition** (nor `vbmeta`).
2. Always back up `boot`, `dtbo`, `recovery`, `vbmeta`.
3. Always use the Windows script `scripts/flash-boot-adb.ps1` (WSL adb cannot see the device).
4. Do not use Odin for `boot` unless you know exactly what you are doing.

## 1. Preparation

- Tablet in **Lineage Recovery** (Power + VolumeUp → "Recovery").
- Windows PC with `adb` in `C:\adb\` (or on PATH).
- Battery > 50%. Working data cable.

```powershell
adb devices -l
# <SERIAL>    recovery ...
```

## 2. Automatic backup

The script backs up by itself:

```powershell
.\scripts\flash-boot-adb.ps1 -Image .\artifacts\boot.img -Serial <SERIAL>
```

It:
1. `dd`s `/dev/block/by-name/boot` → `backups/live/boot-<timestamp>.img`
2. verifies the backup SHA256
3. pushes the image to `/tmp/boot.img`
4. verifies the remote SHA256
5. `dd`s to `/dev/block/by-name/boot`
6. **reads back and compares byte-by-byte**

If you see `verifica OK: partizione boot identica all'immagine`, the flash succeeded.

## 3. Boot and verify

```powershell
adb reboot
# wait ~60s, then via SSH:
ssh gta4xlwifi@<TABLET_IP>
# default password: 147147
uname -r        # 7.3.0-gta4xl-upstream
cat /etc/os-release
```

## 4. Rollback

If the new boot does not start:

1. Reboot into recovery.
2. Flash the backup:

```powershell
.\scripts\flash-boot-adb.ps1 -Image .\backups\live\boot-<timestamp>.img -Serial <SERIAL>
```

Or flash the known-good boot included in the release:

```powershell
.\scripts\flash-boot-adb.ps1 -Image .\release\boot.img -Serial <SERIAL>
```

## 5. Installing the sterile ROM (rootfs)

The sterile zip contains `rootfs.tar.gz` to extract into the root partition
(`/dev/block/sda32` from recovery, `/dev/sda32` at runtime):

```powershell
adb shell "mkdir -p /mnt/rootfs; mount -t ext4 -o rw /dev/block/sda32 /mnt/rootfs"
adb push rootfs.tar.gz /tmp/rootfs.tar.gz
adb shell "tar -xzf /tmp/rootfs.tar.gz -C /mnt/rootfs/home/gta4xlwifi/"
adb reboot
```

See [STERILE-ROM.md](STERILE-ROM.md).

## 6. Partitions (reference)

| Partition | Device at runtime | Use |
|---|---|---|
| boot | `/dev/sda12` | boot.img (flash here) |
| rootfs | `/dev/sda32` | pmOS rootfs |
| dtbo / recovery / vbmeta | — | **DO NOT TOUCH** |
