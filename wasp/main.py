# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

import wasp
# from gadgetbridge import *
wasp._is_in_simulation = False
wasp.watch.hrs.disable()
wasp.system.schedule()
