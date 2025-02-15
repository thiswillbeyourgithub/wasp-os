# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson
"""Gadgetbridge/Bangle.js protocol

Currently implemented messages are:

 * t:"notify", id:int, src,title,subject,body,sender,tel:string - new
   notification
 * t:"notify-", id:int - delete notification
 * t:"alarm", d:[{h,m},...] - set alarms
 * t:"find", n:bool - findDevice
 * t:"vibrate", n:int - vibrate
 * t:"weather", temp,hum,txt,wind,loc - weather report
 * t:"musicstate", state:"play/pause",position,shuffle,repeat - music
   play/pause/etc
 * t:"musicinfo", artist,album,track,dur,c(track count),n(track num) -
   currently playing music track
 * t:"call", cmd:"accept/incoming/outgoing/reject/start/end", name: "name", number: "+491234" - call
"""

import io
import json
import sys
import wasp

# JSON compatibility
null = None
true = True
false = False


def _info(msg):
    json.dump({'t': 'info', 'msg': msg}, sys.stdout)
    sys.stdout.write('\r\n')


def _error(msg):
    json.dump({'t': 'error', 'msg': msg}, sys.stdout)
    sys.stdout.write('\r\n')


def filter_notifications(msg):
    """
    only display notifications that contain one of the element of
    wasp._notif_filter
    """
    if not hasattr(wasp.system, "_notif_filter"):
        return True
    for check in wasp.system._notif_filter:
        for k, v in msg.items():
            if check.lower() in str(k).lower() or check.lower() in str(v).lower():
                return True
    return False


def vibration_timeout():
    """
    simple function called a few second after the 'find' command was sent to
    make sure the watch does not vibrate for too long if the watch is not
    found.
    """
    if not wasp.watch.vibrator.pin.value():  # is vibrating
        wasp.watch.vibrator.pin(True)


def GB(cmd):
    "execute code depending on what gadget bridge asks"
    task = cmd['t']
    del cmd['t']

    try:
        if task == 'find':
            wasp.system.set_alarm(
                    wasp.watch.rtc.time() + 5,
                    vibration_timeout)
            wasp.watch.vibrator.pin(not cmd['n'])
        elif task == 'notify':
            if filter_notifications(cmd):
                id = cmd["id"]
                del cmd["id"]
                wasp.watch.vibrator.pulse(ms=wasp.system.notify_duration)
                wasp.system.notify(id, cmd)
        elif task == 'notify-':
            wasp.system.unnotify(cmd['id'])
        elif task == 'call':
            if cmd["cmd"] not in ["incoming", "outgoing"]:
                raise Exception("Untested call notif")
            name = cmd["name"] if "name" in cmd else ""
            number = cmd["number"] if "number" in cmd else ""
            rest = "/".join(["{}:{}".format(k, v)
                             for k, v in cmd.items()
                             if k not in ["number", "name"]])
            del cmd
            wasp.system.notify(task, {
                "title": task.upper(),
                "body": "{} at {}\n{}".format(name, number, rest),
                })
            if not wasp.system.notify_level <= 1:  # silent mode
                import time
                wasp.system.wake()
                wasp.system.switch(wasp.system.notifier)
                for i in range(3):
                    wasp.watch.vibrator.pulse(ms=wasp.system.notify_duration)
                    time.sleep(0.3)
                del time
        elif task == 'musicstate':
            wasp.system.toggle_music(cmd)
        elif task == 'musicinfo':
            wasp.system.set_music_info(cmd)
        elif task == 'weather':
            wasp.system.set_weather_info(cmd)
        else:
            error_to_notification(
                    title="GB_no_task",
                    msg='GadgetBridge task not implemented: "{}": "{}"'.format(
                        task,
                        "/".join(["{}:{}".format(k, v)
                                  for k, v in cmd.items()])
                        ))
    except Exception as e:
        msg = io.StringIO()
        sys.print_exception(e, msg)
        _error(msg.getvalue())
        msg.close()
        error_to_notification(
                title="GB_except",
                msg="GB error: {} -  {}:{}".format(
                    e,
                    task,
                    "/".join(["{}:{}".format(k, v) for k, v in cmd.items()])
                    ))


def error_to_notification(title, msg):
    wasp.system.notify(title, {"title": title, "body": msg})
    if not wasp.system.notify_level <= 1:  # silent mode
        wasp.watch.vibrator.pulse(ms=wasp.system.notify_duration)
