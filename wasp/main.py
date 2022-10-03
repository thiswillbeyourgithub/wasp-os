# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

import wasp
 from gadgetbridge import *

# to differentiate from simulator
wasp._is_in_simulation = False

# disable heart rate flash if stuck
wasp.watch.hrs.disable()

# load previous settings
wasp.system.notify_level = int(wasp.system.get("notify_level"))
wasp.system.brightness = int(wasp.system.get("brightness"))
wasp.system.hrm_freq = int(wasp.system.get("hrm_freq"))
wasp.system.battery_unit = wasp.system.get("battery_unit")
wasp.system.units = wasp.system.get("units")

# start watch
wasp.system.schedule()
