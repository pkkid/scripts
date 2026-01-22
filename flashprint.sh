#!/bin/bash
# FlashPrint wrapper to clean up VPN interfaces.
#
# This script checks for active VPN connections and cleans up VPN network
# interfaces before launching FlashPrint. FlashPrint requires VPN to be
# disconnected to function properly.
#
# Usage:
#  ./flashprint.sh [flashprint_arguments]
#
# The script will:
#   1. Check if vpn0 or gpd0 interfaces are UP (active)
#   2. Show error dialog if VPN is active and exit
#   3. Remove any DOWN VPN interfaces (vpn0, gpd0)
#   4. Launch FlashPrint with proper Qt/Wayland configuration

# Check if VPN interfaces are UP (active)
if ip link show vpn0 2>/dev/null | grep -q "state UP"; then
  zenity --error --text="Please disconnect your VPN before using FlashPrint" --title="VPN Active"
  exit 1
fi
if ip link show gpd0 2>/dev/null | grep -q "state UP"; then
  zenity --error --text="Please disconnect your VPN before using FlashPrint" --title="VPN Active"
  exit 1
fi

# Remove the DOWN interfaces if they exist
sudo ip link delete vpn0 2>/dev/null
sudo ip link delete gpd0 2>/dev/null

# Launch FlashPrint with proper Qt platform
QT_QPA_PLATFORM=xcb GDK_BACKEND=wayland /usr/share/FlashPrint5/FlashPrint "$@" &
