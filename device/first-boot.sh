#!/bin/sh
# First-boot setup for the sterile ROM. Runs once as root (OpenRC local service).
# Creates the default user, regenerates machine-id and SSH host keys,
# installs onboard config + SSH toggle, then removes itself from boot.
set -e

MARKER=/etc/gta4xlwifi-first-boot-done
[ -e "$MARKER" ] && exit 0

USERNAME=gta4xlwifi
DEFAULT_PASSWORD=147147

echo "gta4xlwifi first-boot setup..."

# 1) Regenerate machine-id (unique per device)
rm -f /etc/machine-id /var/lib/dbus/machine-id
dbus-uuidgen --ensure=/etc/machine-id 2>/dev/null || cat /proc/sys/kernel/random/uuid > /etc/machine-id
cp /etc/machine-id /var/lib/dbus/machine-id 2>/dev/null || true

# 2) Regenerate SSH host keys (installed but SSH disabled by default)
rm -f /etc/ssh/ssh_host_*
ssh-keygen -A >/dev/null 2>&1 || true

# 3) Create default user if missing
if ! id "$USERNAME" >/dev/null 2>&1; then
  useradd -m -s /bin/bash -G sudo,audio,video,netdev,plugdev,bluetooth,dialout "$USERNAME"
  echo "$USERNAME:$DEFAULT_PASSWORD" | chpasswd
  # Force password change at first interactive login
  chage -d 0 "$USERNAME" 2>/dev/null || true
fi

# 4) Install device helpers
install -m 755 /usr/local/share/ssh-toggle.sh /usr/local/bin/ssh-toggle.sh 2>/dev/null || true
install -m 644 /usr/local/share/ssh-toggle.desktop /usr/share/applications/ssh-toggle.desktop 2>/dev/null || true
if [ -d /home/$USERNAME ]; then
  mkdir -p /home/$USERNAME/.config/onboard
  install -m 644 /usr/local/share/onboard.conf /home/$USERNAME/.config/onboard/onboard.conf 2>/dev/null || true
  chown -R "$USERNAME:$USERNAME" /home/$USERNAME/.config 2>/dev/null || true
fi

# 5) Make sure SSH is NOT started at boot
rc-update del sshd default 2>/dev/null || true

echo "done" > "$MARKER"
echo "gta4xlwifi first-boot setup complete."
