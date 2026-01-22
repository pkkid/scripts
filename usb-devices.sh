#!/bin/bash
# List all USB devices with their device paths and serial numbers.
#
# This script scans the /sys filesystem for USB devices and displays them
# with their device node paths (/dev/...) and serial identifiers. Useful
# for identifying USB devices before mounting or accessing them.
#
# Usage:
#  ./usb-devices.sh
#
# Output format:
#  /dev/sdb - Kingston_DataTraveler_3.0_60A44C413E64F5F0FB9C3F1A-0:0
#  /dev/ttyUSB0 - FTDI_FT232R_USB_UART_A50285BI
#
# The script uses udevadm to query device information from the kernel's
# device manager, filtering out bus entries and devices without serial numbers.

for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
    (
        syspath="${sysdevpath%/dev}"
        devname="$(udevadm info -q name -p $syspath)"
        [[ "$devname" == "bus/"* ]] && exit
        eval "$(udevadm info -q property --export -p $syspath)"
        [[ -z "$ID_SERIAL" ]] && exit
        echo "/dev/$devname - $ID_SERIAL"
    )
done
