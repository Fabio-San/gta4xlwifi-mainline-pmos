#!/bin/busybox sh
# Configura gadget RNDIS sul UDC 13200000.usb
G=/sys/kernel/config/usb_gadget/g1
mkdir -p "$G"
echo 0x18d1 > "$G/idVendor"
echo 0x4ee7 > "$G/idProduct"
mkdir -p "$G/configs/c.1/strings/0x409"
echo 0 > "$G/configs/c.1/MaxPower"
mkdir -p "$G/functions/rndis.usb0"
ln -s "$G/functions/rndis.usb0" "$G/configs/c.1/rndis.usb0" 2>/dev/null
UDC=$(ls /sys/class/udc | head -1)
echo "$UDC" > "$G/UDC"
echo "pmos-init: RNDIS bound $UDC" > /dev/kmsg
