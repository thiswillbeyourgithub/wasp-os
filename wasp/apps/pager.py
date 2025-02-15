# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

"""Pager applications
~~~~~~~~~~~~~~~~~~~~~

The pager is used to present text based information to the user. It is
primarily intended for notifications but is also used to provide debugging
information when applications crash.
"""

import wasp
import icons
import fonts

import io
import sys

class PagerApp():
    """Show a long text message in a pager."""
    NAME = 'Pager'
    ICON = icons.app

    def __init__(self, msg):
        self._msg = msg
        self._scroll = wasp.widgets.ScrollIndicator()

    def foreground(self):
        """Activate the application."""
        wasp.system.request_event(wasp.EventMask.SWIPE_UPDOWN)
        self._redraw()

    def background(self):
        """De-activate the application."""
        self._chunks = None
        self._numpages = None

    def swipe(self, event):
        """Swipe to page up/down."""
        if event[0] == wasp.EventType.UP:
            if self._page >= self._numpages:
                wasp.system.navigate(wasp.EventType.BACK)
                return
            self._page += 1
        else:
            if self._page <= 0:
                wasp.watch.vibrator.pulse()
                return
            self._page -= 1
        self._draw()

    def _redraw(self):
        """Redraw from scratch (jump to the first page)"""
        self._page = 0
        self._chunks = wasp.watch.drawable.wrap(self._msg, 240)
        self._numpages = (len(self._chunks) - 2) // 9
        self._draw()

    def _draw(self):
        """Draw a page from scratch."""
        mute = wasp.watch.display.mute
        draw = wasp.watch.drawable

        mute(True)
        draw.set_color(0xffff)
        draw.fill()

        page = self._page
        i = page * 9
        j = i + 11
        chunks = self._chunks[i:j]
        draw.set_font(fonts.sans18)
        for i in range(len(chunks)-1):
            sub = self._msg[chunks[i]:chunks[i+1]].rstrip()
            draw.string(sub, 0, 24*i)
        draw.reset()

        scroll = self._scroll
        scroll.up = page > 0
        scroll.down = page < self._numpages
        scroll.draw()

        mute(False)

class NotificationApp(PagerApp):
    NAME = 'Notifications'

    def __init__(self):
        super().__init__('')
        self.confirmation_view = wasp.widgets.ConfirmationView()

    def foreground(self):
        notes = wasp.system.notifications
        note = notes.pop(next(iter(notes)))
        title = note['title'] if 'title' in note else 'Untitled'
        body = note['body'] if 'body' in note else ''
        rest = "/".join(["{}:{}".format(k, v)
                         for k, v in note.items()
                         if k not in ["title", "body"]])
        if rest != "":
            body += "\n({})".format(rest[:-1])
        self._msg = '{}:\n{}'.format(title, body)

        wasp.system.request_event(wasp.EventMask.TOUCH)
        super().foreground()

    def background(self):
        self.confirmation_view.active = False
        super().background()

    def swipe(self, event):
        if self.confirmation_view.active:
            if event[0] == wasp.EventType.UP:
                self.confirmation_view.active = False
                self._draw()
                return
        else:
            if event[0] == wasp.EventType.DOWN and self._page == 0:
                self.confirmation_view.draw('Clear notifications?')
                return

        super().swipe(event)

    def touch(self, event):
        if self.confirmation_view.touch(event):
            if self.confirmation_view.value:
                wasp.system.notifications = {}
                wasp.system.navigate(wasp.EventType.BACK)
            else:
                self._draw()

class CrashApp():
    """Crash handler application.

    This application is launched automatically whenever another
    application crashes. Our main job it to indicate as loudly as
    possible that the system is no longer running correctly. This
    app deliberately enables inverted video mode in order to deliver
    that message as strongly as possible.
    """
    def __init__(self, exc):
        """Capture the exception information.

        This app does not actually display the exception information
        but we need to capture the exception info before we leave
        the except block.
        """
        msg = io.StringIO()
        sys.print_exception(exc, msg)
        self._msg = msg.getvalue()
        msg.close()

    def foreground(self):
        """Indicate the system has crashed by drawing a couple of bomb icons.

        If you owned an Atari ST back in the mid-eighties then I hope you
        recognise this as a tribute a long forgotten home computer!
        """
        wasp.watch.display.invert(False)
        draw = wasp.watch.drawable
        draw.blit(icons.bomb, 0, 104)
        draw.blit(icons.bomb, 32, 104)

        wasp.system.request_event(wasp.EventMask.SWIPE_UPDOWN |
                                  wasp.EventMask.SWIPE_LEFTRIGHT)

    def background(self):
        """Restore a normal display mode.

        Conceal the display before the transition otherwise the inverted
        bombs get noticed by the user.
        """
        wasp.watch.display.mute(True)
        wasp.watch.display.invert(True)

    def swipe(self, event):
        """Show the exception message in a pager."""
        wasp.system.switch(PagerApp(self._msg))
