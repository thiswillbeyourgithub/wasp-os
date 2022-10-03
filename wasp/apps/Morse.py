# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2021 Francesco Gazzetta

"""Morse translator and notepad
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This app is a simple morse translator that also doubles as a notepad.
Swipe up for a line, swipe down for a dot, tap for end letter, double tap for
end word. Swipe right for space, twice for newline. Swipe left to delete
character.
Up to 7 lines of translation will be displayed on a 240x240 screen, and old
lines will be deleted.
There is a preview of the next letter at the bottom of the screen.


.. figure:: res/MorseApp.png
    :width: 179
"""

import wasp
import icons
import fonts
from math import floor
from micropython import const


_WIDTH = const(240)
_HEIGHT = const(240)
# No easy way to make this depend on _WIDTH
_MAXINPUT = const(16)

# These two need to match
_FONTH = const(18)
_FONT = fonts.sans18

# Precomputed for efficiency
_LINEH = const(30) # int(_FONTH * 1.25)
_MAXLINES = const(8) # floor(_HEIGHT / _LINEH) - 1 # the "-1" is the input line

# The morse lookup table, represented as a flattened binary tree.
# The head is the value of the node, the tail are the subtrees:
# left half of the tail = the next symbol is a dot
# right half of the tail = the next symbol is a line
_CODE = " eish54v?3uf????2arl?????wp??j?1tndb6?x??kc??y??mgz7?q??o?8??90"
# uppercase:
#_CODE = " EISH54V?3UF????2ARL?????WP??J?1TNDB6?X??KC??Y??MGZ7?Q??O?8??90"
# letters only:
#_CODE = " EISHVUF?ARL?WPJTNDBXKCYMGZQO??"

class MorseApp():
    NAME = 'Morse'
    # 2-bit RLE, 96x64, generated from res/morse_icon.png, 143 bytes
    ICON = (
        b'\x02'
        b'`@'
        b'?\xff\xff\xff\xff\x13\xc4?\x1c\xc6?\x1b\xc6?\x1b\xc6'
        b'?\x1a\xc8?\x19\xc8?\x18\xca?\x17\xc4\x02\xc4?\x17'
        b'\xc4\x02\xc4?\x16\xc5\x02\xc5?\x15\xc4\x04\xc4?\x15\xc4'
        b'\x04\xc4?\x14\xc4\x06\xc4?\x13\xc4\x06\xc4?\x12\xc5\x06'
        b'\xc5?\x11\xc4\x08\xc4?\x11\xd0?\x10\xd2?\x0f\xd2?'
        b'\x0e\xc5\n\xc4?\x0e\xc4\x0c\xc4?\r\xc4\x0c\xc4?\x0c'
        b'\xc5\x0c\xc5?\x0b\xc4\x0e\xc4?\x0b\xc4\x0e\xc4?\n\xc4'
        b'\x10\xc4?\xff\xff\xff\xff\x83\xc4\x0e\xda4\xc4\x0e\xda4'
        b'\xc4\x0e\xda4\xc4\x0e\xda?\xff\xff\xff\xfe'
    )

    def __init__(self):
        self.letter = ""
        self.text = [""]

    def foreground(self):
        try:
            text = [t.strip() for t in wasp.system.get("morse") if t.strip() != ""]
            if len(text) > _MAXLINES:
                self.text = text[-_MAXLINES:]
                self.buffer = text[:-_MAXLINES]
        except:
            self.text = [""]
            self.buffer = []
        self._draw()
        wasp.system.request_event(wasp.EventMask.TOUCH |
                                  wasp.EventMask.SWIPE_LEFTRIGHT |
                                  wasp.EventMask.SWIPE_UPDOWN)

    def background(self):
        wasp.system.set("morse", self.buffer + self.text)

    def swipe(self, event):
        self.adjust_buffer()
        if event[0] == wasp.EventType.LEFT:
            if self.letter == "":
                if self.text[-1] == "" and len(self.text) > 1:
                    self.text.pop(-1)  # remove last line
                    self._draw()
                else:
                    self.text[-1] = self.text[-1][:-1]  # remove last character
                    self._update()
            self.letter = ""
        elif event[0] == wasp.EventType.RIGHT:
            if self.text[-1].endswith(" "):
                self.text.append("")   # add nothing but on a new line
                self._draw()
            else:
                self._add_letter(" ")  # add space
        else:
            if len(self.letter) < _MAXINPUT:
                self.letter += "-" if event[0] == wasp.EventType.UP else "."
                self.adjust_buffer()
                self._update()

    def touch(self, event):
        self._add_letter(self._lookup(self.letter))

    def _add_letter(self, addition):
        merged = self.text[-1] + addition
        # Check if the new text overflows the screen and add a new line if that's the case
        split = wasp.watch.drawable.wrap(merged, _WIDTH)
        if len(split) > 2:
            self.text.append(self.text[-1][split[1]:split[2]] + addition)
            self.text[-2] = self.text[-2][split[0]:split[1]]
            # Ideally a full refresh should be done only when we exceed
            # _MAXLINES, but this should be fast enough
            self._draw()
        else:
            self.text[-1] = merged
        self.letter = ""
        self.adjust_buffer()
        self._update()

    def adjust_buffer(self):
        while len(self.text) > _MAXLINES:
            self.buffer.append(self.text.pop(0))
        if len(self.text) < _MAXLINES and len(self.buffer) > 0:
            self.text.insert(0, self.buffer.pop())

    def _draw(self):
        """Draw the display from scratch"""
        draw = wasp.watch.drawable
        draw.fill()
        self.adjust_buffer()
        for i, line in enumerate(self.text):
            draw.string(line.replace(" ", "."), 0, _LINEH * i)
        self._update()

    def _update(self):
        """Update the dynamic parts of the application display, specifically the
        input line and last line of the text.
        The full text area is updated in _draw() instead."""
        draw = wasp.watch.drawable
        draw.fill(None, x=0, y=_LINEH*(len(self.text)-1), w=_WIDTH, h=_LINEH)  # erase last line
        draw.string("{} {}".format(self.letter, self._lookup(self.letter)), 0, _HEIGHT - _FONTH, width=_WIDTH, right=True)  # draw guess
        draw.string(self.text[-1].replace(" ", "."), 0, _LINEH*(len(self.text)-1))  # draw last line

    def _lookup(self, s):
        i = 0 # start of the subtree (current node)
        l = len(_CODE) # length of the subtree

        for c in s:
            # first discard the head, which represent the previous guess
            i += 1
            l -= 1

            # Check if we can no longer bisect while there are still dots/lines
            if l <= 0: return "?"

            # Update the bounds to the appropriate subtree
            # (left or right of the tail).
            # The length will always be half:
            l //= 2
            # The index will be either at the beginning of the tail,
            # or at its half, in which case we subtract the current length,
            # which is half of the old length:
            if c == "-": i += l
        return _CODE[i]
