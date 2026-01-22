#!/bin/bash
#
# Configure DISPLAY variable for X11 forwarding from WSL to Windows.
#
# This script sets up the DISPLAY environment variable to connect to an
# X server running on the Windows host (e.g., VcXsrv, Xming, or X410).
# It automatically detects the Windows host IP address from WSL's routing
# table and configures X11 display settings.
#
# Usage:
#  source ./wsl-xdisplay.sh
#  # or add to ~/.bashrc:
#  # source ~/path/to/wslxdisplay.sh
#
# Example:
#  source wslxdisplay.sh
#  xclock  # Test X11 forwarding with a simple clock app
#
# Requirements:
#  - X server running on Windows (VcXsrv, Xming, X410, etc.)
#  - X server configured to allow connections from WSL
#  - Firewall rules allowing X11 connections
#
# The script also sets XCURSOR_SIZE to fix cursor display issues in WSL.

# Sets the DISPLAY for an X server running on Windows
xdisplay=$(ip route|awk '/^default/{print $3}' | head -n 1)
export DISPLAY=$xdisplay:0.0
export XCURSOR_SIZE=10    # Fix1 cursor size
# xrdb -load ~/.Xresources  # Fix2 cursor size
