# The MIT License (MIT)
#
# Copyright (c) 2019 Kevin J. Walters
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_midi.pitch_bend`
================================================================================

Pitch Bend Change MIDI message.


* Author(s): Kevin J. Walters

Implementation Notes
--------------------

"""

from .midi_message import MIDIMessage

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


class PitchBend(MIDIMessage):
    """Pitch Bend Change MIDI message.

    :param int pitch_bend: A 14bit unsigned int representing the degree of
        bend from 0 through 8192 (midpoint, no bend) to 16383.
    """

    _STATUS = 0xe0
    _STATUSMASK = 0xf0
    LENGTH = 3

    def __init__(self, pitch_bend, *, channel=None):
        self.pitch_bend = pitch_bend
        super().__init__(channel=channel)
        if not 0 <= self.pitch_bend <= 16383:
            raise self._EX_VALUEERROR_OOR

    def __bytes__(self):
        return bytes([self._STATUS | (self.channel & self.CHANNELMASK),
                      self.pitch_bend & 0x7f,
                      (self.pitch_bend >> 7) & 0x7f])

    @classmethod
    def from_bytes(cls, msg_bytes):
        return cls(msg_bytes[2] << 7 | msg_bytes[1],
                   channel=msg_bytes[0] & cls.CHANNELMASK)

PitchBend.register_message_type()
