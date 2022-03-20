# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

"""Generic lithium ion battery driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import micropython
from machine import Pin, ADC

class Battery(object):
    """Generic lithium ion battery driver.

    .. automethod:: __init__
    """

    def __init__(self, battery, charging, power=None):
        """Specify the pins used to provide battery status.

        :param Pin battery:  The ADC-capable pin that can be used to measure
                             battery voltage.
        :param Pin charging: A pin (or Signal) that reports the charger status.
        :param Pin power:    A pin (or Signal) that reports whether the device
                             has external power, defaults to None (which means
                             use the charging pin for power reporting too).
        """
        self._battery = ADC(battery)
        self._charging = charging
        self._power = power
        self.levels = set()

    @micropython.native
    def charging(self):
        """Get the charging state of the battery.

        :returns: True if the battery is charging, False otherwise.
        """
        return self._charging.value()

    def power(self):
        """Check whether the device has external power.

        :returns: True if the device has an external power source, False
                  otherwise.
        """
        if self._power:
            return self._power.value()
        return self._charging.value()

    def voltage_mv(self):
        """Read the battery voltage.

        Assumes a 50/50 voltage divider and a 3.3v power supply

        :returns: Battery voltage, in millivolts.
        """
        raw = self._battery.read_u16()
        return (2 * 3300 * raw) // 65535

    def level(self):
        """Estimate the battery level.

        The current the estimation approach is extremely simple. It is assumes
        the discharge from 4v to 3.5v is roughly linear and 4v is 100% and
        that 3.5v is 5%. Below 3.5v the voltage will start to drop pretty
        sharply so we will drop from 5% to 0% pretty fast... but we'll
        live with that for now.

        The last few values are kept in a cache and only the minium of those
        few values is shown to the user, this is to avoid the battery level
        going up and down values because of the lack of precision of the mv.
        Note that this will underestimate battery level.

        :returns: Estimate battery level in percent.
        """
        mv = self.voltage_mv()
        level = ((19 * mv) // 100) - 660
        levels = self.levels
        if level >= 100:
            levels = set([100])
        elif level <= 0:
            levels = set([0])
        elif level not in levels:
            levels.add(level)
            while len(levels) > 3:
                levels.remove(max(levels))
        return min(levels)
