#!/usr/bin/env python3
"""
Display hardware sensor readings from Linux sysfs.

This script reads hardware sensor information from the Linux kernel's hwmon
interface (/sys/class/hwmon) and displays temperature, voltage, and fan speed
readings. It automatically discovers all available sensors and formats the
output with appropriate units.

Usage:
  ./sensors.py

The script will output:
  - Chip/sensor names with their sysfs paths
  - Temperature readings in degrees Celsius (°C)
  - Voltage readings in Volts (V)
  - Fan speeds in RPM
  - Custom sensor labels when available
"""
import glob
import re
from pathlib import Path


def natural_sort_key(path):
    """ Sort key function for natural/numerical ordering of filenames. """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', Path(path).name)]


def get_name(path):
    """ Get the chip name from the hwmon directory. """
    try:
        return path.read_text().strip()
    except Exception:
        return 'Unknown'


def get_label(path):
    """ Get the sensor label from the hwmon directory. """
    try:
        return path.read_text().strip()
    except Exception:
        return base_name


if __name__ == '__main__':
    # Iterate over all hwmon directories
    print()
    for hwmon_dir in sorted(glob.glob('/sys/class/hwmon/hwmon*')):
        chip_name = get_name(Path(f'{hwmon_dir}/name'))
        print(f'\033[36m{chip_name} ({hwmon_dir})\033[0m')
        for input_file in sorted(glob.glob(f'{hwmon_dir}/*_input'), key=natural_sort_key):
            try:
                base_name = Path(input_file).stem.replace('_input', '')
                label = get_label(Path(f'{hwmon_dir}/{base_name}_label'))
                value = float(Path(input_file).read_text().strip())
                if base_name.startswith('temp'):
                    value_display, unit = f'{value / 1000:.2f}', '°C'
                elif base_name.startswith('in'):
                    value_display, unit = f'{value / 1000:.2f}', 'V'
                else:
                    value_display, unit = str(int(value)), ''
                print(f'  {Path(input_file).name:<15} {label:<15} {value_display} {unit}')
            except Exception:
                pass
    print()
