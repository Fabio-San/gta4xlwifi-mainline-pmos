#!/bin/sh
# SSH toggle for gta4xlwifi — GUI (zenity) and CLI.
# Keeps SSH disabled by default; the user decides when to enable it.
set -e

TITLE="SSH server (gta4xlwifi)"

cli_help() {
  cat <<'EOF'
Usage: ssh-toggle.sh [status|start|stop|enable|disable]
  status   show current SSH state
  start    start sshd now
  stop     stop sshd now
  enable   start sshd now AND at every boot
  disable  stop sshd and remove from boot
EOF
}

get_state() {
  running=$(rc-service sshd status 2>/dev/null | grep -qi started && echo running || echo stopped)
  enabled=$(rc-update show default 2>/dev/null | grep -q sshd && echo enabled || echo disabled)
  echo "SSH: $running, at boot: $enabled"
}

case "${1:-}" in
  status) get_state; exit 0 ;;
  start)  sudo rc-service sshd start;  get_state; exit 0 ;;
  stop)   sudo rc-service sshd stop;   get_state; exit 0 ;;
  enable) sudo rc-service sshd start; sudo rc-update add sshd default >/dev/null; get_state; exit 0 ;;
  disable) sudo rc-service sshd stop; sudo rc-update del sshd default >/dev/null; get_state; exit 0 ;;
  -h|--help|help) cli_help; exit 0 ;;
esac

# GUI mode (no arguments)
if ! command -v zenity >/dev/null 2>&1; then
  cli_help
  exit 1
fi

running=$(rc-service sshd status 2>/dev/null | grep -qi started && echo yes || echo no)
enabled=$(rc-update show default 2>/dev/null | grep -q sshd && echo yes || echo no)

choice=$(zenity --list --title="$TITLE" \
  --text="SSH is currently: $([ "$running" = yes ] && echo RUNNING || echo STOPPED) (boot: $([ "$enabled" = yes ] && echo ENABLED || echo DISABLED))\n\nChoose an action:" \
  --column="Action" \
  "Start SSH now" \
  "Stop SSH now" \
  "Enable SSH at boot" \
  "Disable SSH at boot" \
  "Show status" 2>/dev/null) || exit 0

case "$choice" in
  "Start SSH now")      sudo rc-service sshd start ;;
  "Stop SSH now")       sudo rc-service sshd stop ;;
  "Enable SSH at boot") sudo rc-service sshd start; sudo rc-update add sshd default >/dev/null ;;
  "Disable SSH at boot")sudo rc-service sshd stop; sudo rc-update del sshd default >/dev/null ;;
  "Show status")        zenity --info --text="$(get_state)" 2>/dev/null ;;
esac
