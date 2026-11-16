#!/bin/bash
# Reset the Blue mic's USB port when it stops working, without unplugging it.
#
# The Blue mic's mini-USB connector sometimes loses contact and drops off.
# This script does the replug in software by turning its USB port off and on
# again, which makes the kernel connect it from scratch.
#
# It does NOT fix the mic after a reboot. After a reboot the mic shows up in
# PipeWire but records nothing, and only losing power fixes that. Turning the
# port off does not cut its power on this motherboard (tested 2026-11-16), and
# the mic's mute button does not help either, so that case still needs a
# physical replug.
#
# Usage:
#  ./fixmic.sh            # Reset the port only if the mic is not working
#  ./fixmic.sh --force    # Reset the port even if the mic looks fine
#
# How It Works
# ------------
# 1. While the mic is connected, the script saves which USB port it is on to
#    ~/.cache/fixmic-port. Once the mic drops off there is no device left to
#    ask, so this is how it knows which port to reset.
# 2. It checks the mic works by recording a moment of audio from it. A mic
#    that is listed in PipeWire but records nothing counts as broken.
# 3. If the mic is broken (or --force is given), it writes 1 then 0 to the
#    port's disable file, which disconnects and reconnects the port.
# 4. It then waits for the mic to record again, trying the reset a few times
#    since a loose connector does not always catch on the first go.
#
# Requirements:
#  - sudo, to write to the port's disable file
#  - pactl and parec, to find the mic in PipeWire and record from it
#  - Run it once while the mic is connected, so it can learn the port

VENDOR_ID="046d"
PRODUCT_ID="0ab7"
SOURCE_NAME="Blue_Microphones"
PORT_CACHE="$HOME/.cache/fixmic-port"
ATTEMPTS=3
WAIT_SECS=10
OFF_SECS=2

if [[ -n $1 && $1 != "--force" ]]; then
    echo "Invalid argument: $1" >&2
    echo ""
    echo "Usage: $(basename $0) [--force]"
    exit 1
fi

# Print the sysfs path of the Blue mic's USB device, if it is connected
find_device() {
    for dev in /sys/bus/usb/devices/[0-9]*-[0-9]*; do
        [[ -f "$dev/idVendor" ]] || continue
        [[ $(cat "$dev/idVendor") == $VENDOR_ID ]] || continue
        [[ $(cat "$dev/idProduct" 2>/dev/null) == $PRODUCT_ID ]] || continue
        echo "$dev"
        return 0
    done
    return 1
}

# Succeed if the Blue mic is in PipeWire and actually records audio. A mic
# that started up badly can be listed but deliver nothing, so being listed
# is not enough.
mic_works() {
    local source bytes
    source=$(pactl list sources short 2>/dev/null | grep -v monitor | grep "$SOURCE_NAME" | awk '{print $2}' | head -1)
    [[ -n $source ]] || return 1
    bytes=$(timeout 5 parec -d "$source" --raw 2>/dev/null | head -c 4096 | wc -c)
    (( bytes >= 4096 ))
}

# Turn the USB port at $1 off and back on
reset_port() {
    echo 1 | sudo tee "$1/disable" > /dev/null || return 1
    sleep $OFF_SECS
    echo 0 | sudo tee "$1/disable" > /dev/null || return 1
}

# Remember which port the mic is on while it is connected
device=$(find_device)
if [[ -n $device ]]; then
    port=$(readlink -f "$device/port")
    mkdir -p "$(dirname "$PORT_CACHE")"
    echo "$port" > "$PORT_CACHE"
fi

if [[ $1 != "--force" ]] && mic_works; then
    echo "Blue mic is working, nothing to do. Use --force to reset it anyway."
    exit 0
fi

if [[ ! -f $PORT_CACHE ]]; then
    echo "Blue mic is missing and its USB port is not known yet." >&2
    echo "Replug it once, then run this script while it is connected so it can learn the port." >&2
    exit 1
fi

port=$(cat "$PORT_CACHE")
if [[ ! -f "$port/disable" ]]; then
    echo "USB port $port has no disable control, so it cannot be reset." >&2
    exit 1
fi

for attempt in $(seq 1 $ATTEMPTS); do
    echo "Resetting USB port $(basename "$port") (attempt $attempt of $ATTEMPTS)..."
    reset_port "$port" || exit 1

    for second in $(seq 1 $WAIT_SECS); do
        sleep 1
        if mic_works; then
            echo "Blue mic is back."
            exit 0
        fi
    done
done

echo "Blue mic did not come back. Check the cable at the mic, then replug it." >&2
exit 1
