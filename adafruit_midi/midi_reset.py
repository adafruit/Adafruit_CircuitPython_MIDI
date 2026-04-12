# SPDX-FileCopyrightText: 2026 Gary Benson
#
# SPDX-License-Identifier: MIT

"""
`adafruit_midi.midi_reset`
================================================================================

Reset MIDI message.


* Author(s): Gary Benson

Implementation Notes
--------------------

"""

from .midi_message import MIDIMessage

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


class Reset(MIDIMessage):
    """Reset MIDI message."""

    _message_slots = []

    _STATUS = 0xFF
    _STATUSMASK = 0xFF
    LENGTH = 1


Reset.register_message_type()
