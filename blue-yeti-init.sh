#!/bin/bash
# Give snd-usb-audio a few seconds to attempt binding after device detection
# 
# How It Works
# ------------
# 1. On every boot (and on every plug event), the udev rule fires when the Blue
#    Yeti is detected.
# 2. The script waits 3 seconds for snd-usb-audio to attempt binding.
# 3. It then checks whether interface 1-6:1.0 has a driver symlink pointing to
#    snd-usb-audio.
# 4. If unbound: it writes 0 then 1 to authorized, forcing the USB device to
#    power-cycle and re-enumerate — this time with snd-usb-audio already loaded,
#    so it binds immediately.
# 5. If already bound (e.g. on replug while system is running, or on the second
#    enumeration after the reset): the check passes, nothing happens. No
#    infinite loop.
#
# Additional Setup
# ----------------
# This script also requires the folloing udev rule:
# 1. Create the udev rule
#    sudo vim /etc/udev/rules.d/99-blue-yeti-init.rules
#    > ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="0ab7", ENV{DEVTYPE}=="usb_device", RUN+="/usr/bin/systemd-run --no-block /home/pkkid/Projects/scripts/blue-yeti-init.sh"
# 2. Reload udev
#    sudo udevadm control --reload-rules
#
sleep 3
for dev in /sys/bus/usb/devices/[0-9]*-[0-9]*; do
  [-f "$dev/idVendor"] || continue
  ["$(cat "$dev/idVendor")" = "046d"] || continue
  ["$(cat "$dev/idProduct" 2>/dev/null)" = "0ab7"] || continue
  name=$(basename "$dev")
  # Check if audio interface 1.0 is unbound (no snd-usb-audio driver symlink)
  if [ ! -L "/sys/bus/usb/devices/${name}:1.0/driver" ]; then
    # Force USB re-enumeration by toggling the device's authorized state
    echo 0 > "$dev/authorized"
    sleep 1
    echo 1 > "$dev/authorized"
  fi
  break
done
