# STERILE-ROM.md — Sterile ROM contents, account and SSH

> Italian: [STERILE-ROM.it.md](STERILE-ROM.it.md)

## What the zip contains

```
gta4xlwifi-pmos-7.3-<date>.zip
├── boot.img              # known-good boot (SHA d71a7d11…)
├── rootfs.tar.gz         # sterile pmOS rootfs
├── flash-boot-adb.ps1    # Windows flash helper
├── README.txt            # quick instructions
└── SHA256SUMS            # checksums
```

The rootfs is **rebuilt clean**, not copied from a personal backup.

### Included
- Standard empty directories: `Desktop/`, `Downloads/`, `Music/`, `Pictures/`,
  `Templates/`, `Videos/` (structure only, no user files)
- Hardware firmware: `mx140`, `calliope_*`, `AP_*_AUDIO_SLSI`, ACPM plugins
- Kernel modules for `7.3.0-gta4xl-upstream` (if found at build time). The 7.3 config
  is effectively monolithic — all display/audio/WiFi drivers are built-in (`=y`);
  only 8 optional symbols are `=m`, so a module-free rootfs still boots correctly.
- Base XFCE configuration (theme, panel, `modesetting`, `DRI 3`, `PageFlip false`)
- `onboard` virtual keyboard with large keys, auto-started
- SSH server installed but **disabled**
- Default user and first-boot setup script

### Excluded (personal data)
- User files, documents, photos, recordings
- `.gnupg/`, `.dbus/`, `.Xauthority`, shell histories, recent files
- `.nmconnection`, `wpa_supplicant.conf`, any saved WiFi credential, any static IP

### Network addressing (DHCP, not static)
- The RNDIS USB gadget (`tools/setup-rndis.sh`) only binds the USB gadget; it assigns
  **no IP address**. The connected host/router provides the address via DHCP, so SSH
  and USB tethering get an address based on the network in use.
- No static IP, no saved WiFi SSID/password and no `192.168.x.x` address are present
  in the sterile rootfs: there is no hardcoded "home network".
- SSH keys, `machine-id`, system logs, device serial numbers

### Regenerated at first boot
- `/etc/machine-id`
- SSH host keys (unique per device)

## Default account

| Item | Value |
|---|---|
| User | `gta4xlwifi` |
| Password | `147147` |
| Groups | `sudo,audio,video,netdev,plugdev,bluetooth,dialout` |

The user is prompted to change the password on first login. The password is public
by design — change it before connecting to any network.

## SSH — enable / disable

SSH is **not started at boot** for security.

### Via terminal
```bash
# start now
sudo rc-service sshd start
# enable at boot
sudo rc-update add sshd default
# disable at boot
sudo rc-update del sshd default
# stop now
sudo rc-service sshd stop
```

### Via GUI
An "SSH" icon in the XFCE applications menu opens a dialog (zenity) that lets you
start/stop SSH and enable/disable it at boot. This is implemented by
`device/ssh-toggle.sh` + `device/ssh-toggle.desktop`.

## Virtual keyboard

`onboard` is installed and auto-started with XFCE. The config in
`device/onboard.conf` sets large keys for finger use on the tablet. This lets a new
user type the password and create/change an account without a physical keyboard.

## Building the zip

```bash
bash scripts/make-sterile-rom.sh
# requires a sterile rootfs directory prepared with device/first-boot.sh
# output: release/gta4xlwifi-pmos-7.3-<date>.zip
```

The builder verifies that no sensitive patterns are present before packing.
