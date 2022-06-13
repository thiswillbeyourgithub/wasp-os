# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

"""Flashlight
~~~~~~~~~~~~~

Shows a bright screen that you can tap to change brightness or switch to redlight.

.. figure:: res/TorchApp.png
    :width: 179
"""

import wasp
import icons


class TorchApp(object):
    """Trivial flashlight application."""
    NAME = 'Torch'
    ICON = icons.torch

    def foreground(self):
        """Activate the application."""
        self._elapsed = 0
        wasp.system.request_tick(3000)
        wasp.system.request_event(wasp.EventMask.TOUCH)

        self._brightness = wasp.system.brightness
        wasp.system.brightness = 3
        self._ntouch = 1
        wasp.watch.drawable.fill(0xf800)  # red

    def background(self):
        """De-activate the application (without losing original state)."""
        wasp.system.brightness = self._brightness

    def tick(self, ticks):
        wasp.system.keep_awake()
        self._elapsed += 3
        if self._elapsed >= 180:
            wasp.system.sleep()

    def touch(self, event):
        self._ntouch += 1
        self._ntouch %= 6
        wasp.system.brightness = (-self._ntouch) % 3 + 1
        if (-self._ntouch + 1) % 3 == 0:
            if -self._ntouch % 6 < 3:
                wasp.watch.drawable.fill(0xffff)  # white
            else:
                wasp.watch.drawable.fill(0xf800)  # red
