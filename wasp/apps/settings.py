# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020-21 Daniel Thompson

"""Settings application
~~~~~~~~~~~~~~~~~~~~~~~

Allows a very small set of user preferences (including the date and
time) to be set on the device itself.

.. figure:: res/SettingsApp.png
    :width: 179

.. note::

    The settings tool is not expected to comprehensively present every
    user configurable preference. Some are better presented via a
    companion app and some particular exotic ones are perhaps best
    managed with a user-provided ``main.py``.
"""


import wasp
import fonts
import icons

class SettingsApp():
    """Settings application."""
    NAME = 'Settings'
    ICON = icons.settings

    def __init__(self):
        self._already_initialized = False

    def _actual_init(self):
        self._bri_slider = wasp.widgets.Slider(4, 10, 90)
        self._nfy_slider = wasp.widgets.Slider(3, 10, 90)
        self._hrm_slider = wasp.widgets.Slider(5, 10, 90)
        self._hrm_freq_values = (0, 5, 15, 30, 60)
        self._scroll_indicator = wasp.widgets.ScrollIndicator()
        self._HH = wasp.widgets.Spinner(50, 60, 0, 23, 2)
        self._MM = wasp.widgets.Spinner(130, 60, 0, 59, 2)
        self._dd = wasp.widgets.Spinner(20, 60, 1, 31, 1)
        self._mm = wasp.widgets.Spinner(90, 60, 1, 12, 1)
        self._yy = wasp.widgets.Spinner(160, 60, 20, 60, 2)
        self._units = ['Metric', 'Imperial']
        self._units_toggle = wasp.widgets.Button(32, 90, 176, 48, "Change")
        self._batt = ['Percent', 'mV', 'Icon']
        self._battery_toggle = wasp.widgets.Button(32, 90, 176, 48, "Change")
        self._settings = ['Brightness', 'Battery', 'Notification Level', 'Time', 'Date', 'Units', "HRM freq"]
        self._sett_index = 0
        self._current_setting = self._settings[0]
        return True

    def foreground(self):
        if not self._already_initialized:
            self._already_initialized = self._actual_init()
        self._draw()
        wasp.system.request_event(wasp.EventMask.TOUCH | wasp.EventMask.SWIPE_UPDOWN)

    def touch(self, event):
        if self._current_setting == 'Brightness':
            self._bri_slider.touch(event)
            wasp.system.brightness = self._bri_slider.value
            wasp.system.set("brightness", wasp.system.brightness)
        elif self._current_setting == 'Notification Level':
            self._nfy_slider.touch(event)
            wasp.system.notify_level = self._nfy_slider.value + 1
            wasp.system.set("notify_level", wasp.system.notify_level)
        elif self._current_setting == 'Time':
            if self._HH.touch(event) or self._MM.touch(event):
                now = list(wasp.watch.rtc.get_localtime())
                now[3] = self._HH.value
                now[4] = self._MM.value
                wasp.watch.rtc.set_localtime(now)
        elif self._current_setting == 'Date':
            if self._yy.touch(event) or self._mm.touch(event) \
                    or self._dd.touch(event):
                now = list(wasp.watch.rtc.get_localtime())
                now[0] = self._yy.value + 2000
                now[1] = self._mm.value
                now[2] = self._dd.value
                wasp.watch.rtc.set_localtime(now)
        elif self._current_setting == 'Units':
            if self._units_toggle.touch(event):
                wasp.system.units = self._units[(self._units.index(wasp.system.units) + 1) % len(self._units)]
            wasp.system.set("units", wasp.system.units)
        elif self._current_setting == 'Battery':
            if self._battery_toggle.touch(event):
                wasp.system.battery_unit = self._batt[(self._batt.index(wasp.system.battery_unit) + 1) % len(self._batt)]
            wasp.system.set("battery_unit", wasp.system.battery_unit)
        elif self._current_setting == "HRM freq":
            if self._hrm_slider.touch(event):
                wasp.system.hrm_freq = self._hrm_freq_values[self._hrm_slider.value]
                if wasp.system.hrm_freq != 0:
                    wasp.system.set_alarm(wasp.watch.rtc.time() + 60, wasp.system._perdiodic_heart_rate)
            wasp.system.set("hrm_freq", wasp.system.hrm_freq)
        self._update()

    def swipe(self, event):
        """Handle NEXT events by augmenting the default processing by resetting
        the count if we are not currently timing something.

        No other swipe event is possible for this application.
        """
        if event[0] == wasp.EventType.UP:
            self._sett_index += 1
            self._draw()
        elif event[0] == wasp.EventType.DOWN:
            self._sett_index -= 1
            self._draw()

    def _draw(self):
        """Redraw the display from scratch."""
        draw = wasp.watch.drawable
        mute = wasp.watch.display.mute
        self._current_setting = self._settings[self._sett_index % len(self._settings)]
        mute(True)
        draw.fill()
        draw.set_color(wasp.system.theme('bright'))
        draw.set_font(fonts.sans24)
        draw.string(self._current_setting, 0, 6, width=240)
        if self._current_setting == 'Brightness':
            self._bri_slider.value = wasp.system.brightness
        elif self._current_setting == 'Notification Level':
            self._nfy_slider.value = wasp.system.notify_level - 1
        elif self._current_setting == 'Time':
            now = wasp.watch.rtc.get_localtime()
            self._HH.value = now[3]
            self._MM.value = now[4]
            draw.set_font(fonts.sans28)
            draw.string(':', 110, 120-14, width=20)
            self._HH.draw()
            self._MM.draw()
        elif self._current_setting == 'Date':
            now = wasp.watch.rtc.get_localtime()
            self._yy.value = now[0] - 2000
            self._mm.value = now[1]
            self._dd.value = now[2]
            self._yy.draw()
            self._mm.draw()
            self._dd.draw()
            draw.set_font(fonts.sans24)
            draw.string('DD    MM    YY',0,180, width=240)
        elif self._current_setting == 'Units':
            self._units_toggle.draw()
        elif self._current_setting == 'Battery':
            self._battery_toggle.draw()
        self._scroll_indicator.draw()
        self._update()
        mute(False)

    def _update(self):
        draw = wasp.watch.drawable
        draw.set_color(wasp.system.theme('bright'))
        if self._current_setting == 'Brightness':
            if wasp.system.brightness == 3:
                say = "High"
            elif wasp.system.brightness == 2:
                say = "Mid"
            elif wasp.system.brightness == 1:
                say = "Low"
            else:  # == 0
                say = "Very Low"
            self._bri_slider.update()
            draw.string(say, 0, 150, width=240)
        elif self._current_setting == "HRM freq":
            self._hrm_slider.draw()
            draw.string("In minutes", 0, 40, 240)
            val = str(self._hrm_freq_values[self._hrm_slider.value])
            if val == "0":
                val = "OFF"
            draw.string(val, 0, 150, 240)
        elif self._current_setting == 'Notification Level':
            if wasp.system.notify_level == 3:
                say = "High"
            elif wasp.system.notify_level == 2:
                say = "Mid"
            else:
                say = "Silent"
            self._nfy_slider.update()
            draw.string(say, 0, 150, width=240)
        elif self._current_setting == 'Units':
            draw.string(wasp.system.units, 0, 150, width=240)
        elif self._current_setting == 'Battery':
            draw.string(str(wasp.system.battery_unit), 0, 150, width=240)
