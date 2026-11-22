#!/bin/bash
# Build a sterile, bootable pmOS ROM zip for gta4xlwifi.
#
# Usage:
#   bash scripts/make-sterile-rom.sh /path/to/source-rootfs.tar.gz
#
# The source rootfs is a local file (e.g. a backup) and is NEVER stored in this
# repository. The script extracts it, removes all user/personal data, creates the
# default account, installs device helpers, and packs a clean ROM.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATE="$(date +%Y%m%d)"
NAME="gta4xlwifi-pmos-7.3-$DATE"
WORK="$(mktemp -d)"
OUT="$ROOT/release"
BOOT="$ROOT/artifacts/boot-upstream-peripherals-nofallback-persistent.img"
# Fallback: the verified boot image kept in the author's flash/ directory.
if [ ! -f "$BOOT" ]; then
  ALT="/mnt/d/Progetti/Ubuntu Project/flash/mainline-7.3-test/boot-7.3-PMOS-restored.img"
  [ -f "$ALT" ] && BOOT="$ALT"
fi

log() { echo "[sterile] $*"; }

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/source-rootfs.tar.gz" >&2
  echo "  Provide a local pmOS rootfs backup (not included in this repo)." >&2
  exit 1
fi
SRC="$1"
[ -f "$SRC" ] || { echo "Source not found: $SRC" >&2; exit 1; }
[ -f "$BOOT" ] || { echo "Boot image missing: $BOOT (run build first)" >&2; exit 1; }

trap 'sudo rm -rf "$WORK" 2>/dev/null || rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------------------
log "1/7 Extracting source rootfs into a temporary workspace"
mkdir -p "$WORK/rootfs"
tar -xzf "$SRC" -C "$WORK/rootfs" 2>/dev/null || {
  echo "Extraction failed" >&2; exit 1;
}
# The archive may contain a single top-level directory; normalize it.
if [ "$(find "$WORK/rootfs" -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 1 ] && \
   [ "$(find "$WORK/rootfs" -mindepth 1 -maxdepth 1 | wc -l)" -eq 1 ]; then
  SUB="$(find "$WORK/rootfs" -mindepth 1 -maxdepth 1 -type d | head -1)"
  mv "$WORK/rootfs" "$WORK/old"
  mv "$SUB" "$WORK/rootfs"
  rmdir "$WORK/old" 2>/dev/null || true
fi
R="$WORK/rootfs"
[ -f "$R/etc/os-release" ] || { echo "Not a rootfs: /etc/os-release missing" >&2; exit 1; }

# ---------------------------------------------------------------------------
log "2/7 Removing user data, credentials and personal files"
# Remove every home directory except the default one (created fresh below).
find "$R/home" -mindepth 1 -maxdepth 1 ! -name gta4xlwifi -exec rm -rf {} + 2>/dev/null || true
# Remove the build-time user from account files (pmbootstrap created it).
for acct in passwd shadow group gshadow; do
  for suffix in '' '-'; do
    [ -f "$R/etc/$acct$suffix" ] && sed -i '/^fabio:/d' "$R/etc/$acct$suffix"
  done
done
# Remove personal dotfiles / histories / keys wherever they are.
find "$R" \( -name '.bash_history' -o -name '.lesshst' -o -name '.viminfo' \
     -o -name '.gnupg' -o -name '.ssh' -o -name '.xsession-errors*' \
     -o -name '.ICEauthority' -o -name '.Xauthority' -o -name 'id_rsa*' \) \
     -exec rm -rf {} + 2>/dev/null || true
# Remove saved network credentials (empty templates are installed later).
find "$R/etc/NetworkManager/system-connections" -type f -name '*.nmconnection' -delete 2>/dev/null || true
rm -f "$R/etc/wpa_supplicant/wpa_supplicant.conf" 2>/dev/null || true
# Remove system logs, machine-id and SSH host keys (regenerated at first boot).
rm -f "$R/etc/machine-id" "$R/var/lib/dbus/machine-id" 2>/dev/null || true
rm -f "$R/etc/ssh/ssh_host_"* 2>/dev/null || true
# Flush upstream example configs that contain 192.168.x.x templates (not personal data,
# but we remove them so the sterile ROM contains no private-range addresses at all).
for f in /etc/udhcpd.conf /etc/dnsmasq.conf; do
  [ -f "$R$f" ] && printf '# Disabled in sterile ROM - no static/example network addresses.\n' > "$R$f"
done
find "$R/var/log" -type f -exec truncate -s 0 {} + 2>/dev/null || true
# Recreate standard empty user directories.
mkdir -p "$R/home/gta4xlwifi"/{Desktop,Downloads,Music,Pictures,Templates,Videos,Documents}
chown -R 1000:1000 "$R/home/gta4xlwifi" 2>/dev/null || true
chmod 755 "$R/home/gta4xlwifi"

# ---------------------------------------------------------------------------
log "3/7 Installing device helpers (SSH toggle, onboard, WiFi template)"
mkdir -p "$R/usr/local/share" "$R/usr/local/bin"
install -m 755 "$ROOT/device/ssh-toggle.sh" "$R/usr/local/share/ssh-toggle.sh"
install -m 644 "$ROOT/device/ssh-toggle.desktop" "$R/usr/local/share/ssh-toggle.desktop"
install -m 644 "$ROOT/device/onboard.conf" "$R/usr/local/share/onboard.conf"
install -m 644 "$ROOT/device/wpa_supplicant.conf.example" \
  "$R/etc/wpa_supplicant/wpa_supplicant.conf.example" 2>/dev/null || true
install -m 755 "$ROOT/device/first-boot.sh" "$R/etc/local.d/gta4xlwifi-first-boot.start"

# 3b) Kernel modules for our 7.3 build (pmbootstrap rootfs has different ones).
MODSRC="/home/fabio/gta4xl-mainline-build/build/modules_install/lib/modules"
if [ -d "$MODSRC" ]; then
  rm -rf "$R/lib/modules" 2>/dev/null || true
  mkdir -p "$R/lib/modules"
  cp -a "$MODSRC"/* "$R/lib/modules/" 2>/dev/null || true
  echo "7.3 kernel modules installed"
else
  echo "WARNING: 7.3 modules not found at $MODSRC"
fi

# 3c) Xorg config: modesetting + DRI3 + PageFlip false (field-tested on this tablet).
mkdir -p "$R/etc/X11/xorg.conf.d"
cat > "$R/etc/X11/xorg.conf.d/00-gta4xl-display.conf" <<'XEOF'
Section "Device"
    Identifier "Panfrost"
    Driver "modesetting"
    Option "DRI" "3"
    Option "PageFlip" "false"
EndSection
XEOF

# 3d) os-release fallback (some pmbootstrap chroots lack it).
if [ ! -f "$R/etc/os-release" ] && [ ! -f "$R/etc/postmarketos-release" ]; then
  cat > "$R/etc/os-release" <<'OSEOF'
NAME="postmarketOS"
PRETTY_NAME="postmarketOS (gta4xlwifi mainline)"
ID="postmarketos"
ID_LIKE="alpine"
VARIANT_ID="gta4xlwifi-mainline"
OSEOF
fi

# ---------------------------------------------------------------------------
log "4/7 Creating the default user and disabling SSH at boot"
if [ -x "$R/usr/sbin/chroot" ] || [ -x "$R/sbin/chroot" ]; then
  mount --bind /proc "$R/proc" 2>/dev/null || true
  mount --bind /sys "$R/sys" 2>/dev/null || true
  mount --bind /dev "$R/dev" 2>/dev/null || true
  chroot "$R" /bin/sh -c '
    id gta4xlwifi >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo,audio,video,netdev,plugdev,bluetooth,dialout gta4xlwifi
    echo "gta4xlwifi:147147" | chpasswd
    rc-update del sshd default 2>/dev/null || true
  ' 2>/dev/null || log "WARNING: chroot user setup skipped (will run at first boot)"
  umount "$R/proc" "$R/sys" "$R/dev" 2>/dev/null || true
else
  log "WARNING: no chroot available; first-boot script will create the user"
fi

# ---------------------------------------------------------------------------
log "5/7 Verifying no sensitive patterns remain"
# Only genuinely personal identifiers. We deliberately do NOT match generic
# 192.168.x.x / MAC-like strings: those appear in upstream default configs
# (avahi, dnsmasq, openssl, APN database) and are not user data.
SENSITIVE_PATTERN='R52[A-Z0-9]{6,}|/home/fabio|fabio:|fabietto089'
if grep -rIE "$SENSITIVE_PATTERN" "$R" --exclude='*.bin' --exclude='*.so*' \
   --exclude='*.a' --exclude='*.pyc' >"$WORK/sensitive.txt" 2>/dev/null; then
  log "ERROR: sensitive patterns found. Aborting. Matches:"
  head -20 "$WORK/sensitive.txt" >&2
  exit 1
fi
log "No sensitive patterns found."

# ---------------------------------------------------------------------------
log "6/7 Packing rootfs and ROM zip"
mkdir -p "$OUT"
tar -czf "$WORK/rootfs.tar.gz" -C "$WORK" rootfs
cp "$BOOT" "$WORK/boot.img"
cp "$ROOT/scripts/flash-boot-adb.ps1" "$WORK/flash-boot-adb.ps1"
{
  echo "gta4xlwifi-mainline-pmos — sterile ROM"
  echo "Built: $DATE"
  echo "User: gta4xlwifi / password: 147147 (CHANGE IMMEDIATELY)"
  echo "SSH: disabled by default. Enable with the SSH icon or: sudo rc-service sshd start"
  echo "See the GitHub repository docs for build/flash instructions."
} > "$WORK/README.txt"
( cd "$WORK" && sha256sum boot.img rootfs.tar.gz flash-boot-adb.ps1 README.txt > SHA256SUMS )
( cd "$WORK" && zip -q "$OUT/$NAME.zip" boot.img rootfs.tar.gz flash-boot-adb.ps1 README.txt SHA256SUMS )

log "7/7 Done"
ls -lh "$OUT/$NAME.zip"
sha256sum "$OUT/$NAME.zip"
