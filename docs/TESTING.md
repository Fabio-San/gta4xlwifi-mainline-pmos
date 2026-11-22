# TESTING.md — Testing the sterile ROM (UNTESTED build)

> **This ROM has NOT been field-tested as a final package.** The kernel and the
> rootfs configuration were verified separately on an SM-P610, but the sterile
> zip (`gta4xlwifi-pmos-7.3-20261122.zip`) was assembled from a clean pmOS base
> and has never been flashed/booted as a whole by the author. **Flash at your own
> risk, and always back up first.**

> Italian: [TESTING.it.md](TESTING.it.md)

---

## 1. Before you flash (mandatory)

1. Back up `boot`, `dtbo`, `recovery`, `vbmeta` (see [FLASH.md](FLASH.md)).
2. Verify the ROM checksum:
   ```bash
   sha256sum gta4xlwifi-pmos-7.3-20261122.zip
   # expected: f1ed8fb1e823bf52646d033e2a6c989b24b30d5505b3b93ef8d199c245f8e27c
   ```
3. Battery > 50%, tablet in **Lineage Recovery**.

## 2. What to test (in order)

| # | Test | Expected | Pass? |
|---|---|---|---|
| 1 | Flash `boot.img`, extract `rootfs.tar.gz` into `/dev/sda32`, reboot | XFCE desktop appears | ☐ |
| 2 | First boot script | user `gta4xlwifi` created, `machine-id`/SSH keys regenerated | ☐ |
| 3 | Login | user `gta4xlwifi` / password `147147` works | ☐ |
| 4 | Onboard keyboard | appears on screen, large keys, usable | ☐ |
| 5 | WiFi | connects to your network (enter your own credentials) | ☐ |
| 6 | SSH off by default | port 22 closed until enabled | ☐ |
| 7 | SSH via GUI icon | "SSH Server" app in XFCE menu starts it | ☐ |
| 8 | SSH via terminal | `sudo rc-service sshd start` works | ☐ |
| 9 | Audio | stereo speakers play | ☐ |
| 10 | Display/touch | 1200x2000, touch responsive | ☐ |
| 11 | Poweroff/reboot | works via PS_HOLD | ☐ |
| 12 | Change password | `passwd` works; account still usable | ☐ |

## 3. What to report (please include ALL of this)

Open a GitHub **Issue** with the tag `rom-test` and include:

1. **Result**: which tests passed/failed (copy the table above).
2. **Exact error messages** — copy them verbatim (screen, `dmesg`, journal).
3. **Boot image SHA256** actually flashed.
4. **Where it stopped**: recovery? boot logo? login screen? XFCE?
5. **Logs** (attach as files, not pasted inline):
   ```bash
   dmesg > dmesg.txt
   cat /etc/os-release
   cat /var/log/reapply-mobian-patches.log 2>/dev/null
   ```
6. **Device**: SM-P610 or SM-P615, your current ROM before flashing.

> **Do not include** personal data: no serial, MAC, IP, WiFi passwords or keys.

## 4. Known limitations (not bugs to re-report)

These are documented in [KNOWN_ISSUES.md](KNOWN_ISSUES.md): no native mic,
no MFC video decode/encode, no Bluetooth, GPU not smooth, headphone jack untested.

## 5. Rollback

If anything fails, reflash your original `boot.img` backup and restore the data
partition from your own backup. See [FLASH.md](FLASH.md).
