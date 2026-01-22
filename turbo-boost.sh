#!/bin/bash
# Enable or disable Intel Turbo Boost on all CPU cores.
#
# This script uses MSR (Model Specific Register) tools to control the Intel
# Turbo Boost feature by reading and writing to CPU registers. Turbo Boost
# allows the processor to run faster than its base clock speed when thermal
# and power conditions allow.
#
# Usage:
#  ./turbo-boost.sh [enable|disable]
#  ./turbo-boost.sh              # Show current status of all cores
#
# Examples:
#  ./turbo-boost.sh disable      # Disable Turbo Boost on all cores
#  ./turbo-boost.sh enable       # Enable Turbo Boost on all cores
#  ./turbo-boost.sh              # Display current Turbo Boost status
#
# Requirements:
#  sudo apt-get install msr-tools
#
# The script reads MSR register 0x1a0 (IA32_MISC_ENABLE) to check and
# modify the Turbo Boost disable bit (bit 38) for each CPU core.

if [[ -z $(which rdmsr) ]]; then
    echo "msr-tools is not installed. Run 'sudo apt-get install msr-tools' to install it." >&2
    exit 1
fi

if [[ ! -z $1 && $1 != "enable" && $1 != "disable" ]]; then
    echo "Invalid argument: $1" >&2
    echo ""
    echo "Usage: $(basename $0) [disable|enable]"
    exit 1
fi

cores=$(cat /proc/cpuinfo | grep processor | awk '{print $3}')
for core in $cores; do
    if [[ $1 == "disable" ]]; then
        sudo wrmsr -p${core} 0x1a0 0x4000850089
    fi
    if [[ $1 == "enable" ]]; then
        sudo wrmsr -p${core} 0x1a0 0x850089
    fi
    state=$(sudo rdmsr -p${core} 0x1a0 -f 38:38)
    if [[ $state -eq 1 ]]; then
        echo "core ${core}: disabled"
    else
        echo "core ${core}: enabled"
    fi
done
