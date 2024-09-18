# SPDX-FileCopyrightText: 2024 Matthew Badeau
#
# SPDX-License-Identifier: MIT

"""
`adafruit_midi.active_sensing`
================================================================================

Active Sensing MIDI message.


* Author(s): Matthew Badeau

Implementation Notes
--------------------

"""

from .midi_message import MIDIMessage

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


class ActiveSensing(MIDIMessage):
    """Active Sensing MIDI message.

    Active Sensing message is a keepalive message sent every 300 milliseconds
    to tell the bus that the session is still good and alive.
    """

    _STATUS = 0xFE
    _STATUSMASK = 0xFF
    LENGTH = 1
    _slots = []


ActiveSensing.register_message_type()
