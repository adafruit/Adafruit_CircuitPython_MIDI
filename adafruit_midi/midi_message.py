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
`adafruit_midi`
================================================================================

A CircuitPython helper for encoding/decoding MIDI packets over a MIDI or UART connection.


* Author(s): Kevin J. Walters

Implementation Notes
--------------------

**Hardware:**



**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


ALL_CHANNELS = -1

# From C3
# Semitones    A   B   C   D   E   F   G
note_offset = [9, 11, 12, 14, 16, 17, 19]

def channel_filter(channel, channel_spec):
    """
    Utility function to return True iff the given channel matches channel_spec.
    """
    if isinstance(channel_spec, int):
        if channel_spec == ALL_CHANNELS:
            return True
        else:
            return channel == channel_spec
    elif isinstance(channel_spec, tuple):
        return channel in channel_spec
    else:
        raise ValueError("Incorrect type for channel_spec")

# TODO - proper parameter typing and look up how this is done when different types are accepted     
def note_parser(note):
    """
    If note is a string then it will be parsed and converted to a MIDI note (key) number, e.g.
    "C4" will return 60, "C#4" will return 61. If note is not a string it will simply be returned.
    
    Applies a range check to both string and integer inputs.
    """
    midi_note = note
    if isinstance(note, str):
        if len(note) < 2:
            raise ValueError("Bad note format")
        noteidx = ord(note[0].upper()) - 65  # 65 os ord('A')
        if not 0 <= noteidx <= 6:
            raise ValueError("Bad note")
        sharpen = 0
        if note[1] == '#':
            sharpen = 1
        elif note[1] == 'b':
            sharpen = -1
        # int may throw exception here
        midi_note = (int(note[1 + abs(sharpen):]) * 12
                     + note_offset[noteidx]
                     + sharpen)

    return midi_note
        
# TODO TBD: can relocate this class later to a separate file if recommended
class MIDIMessage:
    """
    A MIDI message:
      - Status - extracted from Status byte with channel replaced by 0s
                (high bit always set)
      - Channel - extracted from Status where present (0-15)
      - 0 or more Data Byte(s) - high bit always not set for data
      - _LENGTH is the fixed message length including status or -1 for variable length
      - _ENDSTATUS is the EOM status byte if relevant
    This is an abstract class.
    """
    _STATUS = None
    _STATUSMASK = None
    _LENGTH = None
    _CHANNELMASK = None
    _ENDSTATUS = None
    
    # Each element is ((status, mask), class)
    # order is more specific masks first
    _statusandmask_to_class = []

    @classmethod
    def register_message_type(cls):
        """Register a new message by its status value and mask.
        """
        ### These must be inserted with more specific masks first
        insert_idx = len(MIDIMessage._statusandmask_to_class)
        for idx, m_type in enumerate(MIDIMessage._statusandmask_to_class):
            if cls._STATUSMASK > m_type[0][1]:
                insert_idx = idx
                break

        MIDIMessage._statusandmask_to_class.insert(insert_idx,
                                                   ((cls._STATUS, cls._STATUSMASK), cls))
                        
    # TODO - this needs a lot of test cases to prove it actually works
    # TODO - finish SysEx implementation and find something that sends one
    @classmethod
    def from_message_bytes(cls, midibytes, channel_in):
        """Create an appropriate object of the correct class for the
        first message found in some MIDI bytes.

        Returns (messageobject, start, endplusone, skipped, channel)
        or for no messages, partial messages or messages for other channels
        (None, start, endplusone, skipped, None).
        """

        msg = None
        startidx = 0
        endidx = len(midibytes) - 1
        skipped = 0
        preamble = True
        
        msgstartidx = startidx
        msgendidxplusone = 0
        while True:
            # Look for a status byte
            # Second rule of the MIDI club is status bytes have MSB set
            while msgstartidx <= endidx and not (midibytes[msgstartidx] & 0x80):
                msgstartidx += 1
                if preamble:
                    skipped += 1
            
            preamble = False

            # Either no message or a partial one
            if msgstartidx > endidx:
                ### TODO review exactly when buffer should be discarded
                ### must not discard the first half of a message
                return (None, startidx, endidx + 1, skipped, None)

            status = midibytes[msgstartidx]
            known_message = False
            complete_message = False
            channel_match_orNA = True
            channel = None
            # Rummage through our list looking for a status match
            for sm, msgclass in MIDIMessage._statusandmask_to_class:
                masked_status = status & sm[1]
                if sm[0] == masked_status:
                    known_message = True
                    # Check there's enough left to parse a complete message
                    # this value can be changed later for a var. length msgs
                    complete_message = len(midibytes) - msgstartidx >= msgclass._LENGTH
                    if complete_message:
                        if msgclass._CHANNELMASK is not None:
                            channel = status & msgclass._CHANNELMASK
                            channel_match_orNA = channel_filter(channel, channel_in)

                        bad_termination = False
                        if msgclass._LENGTH < 0:  # indicator of variable length message
                            terminated_message = False
                            msgendidxplusone = msgstartidx + 1
                            while msgendidxplusone <= endidx:
                                if midibytes[msgendidxplusone] & 0x80:
                                    if midibytes[msgendidxplusone] == msgclass._ENDSTATUS:
                                        terminated_message = True
                                    else:
                                        bad_termination = True
                                    break
                                else:
                                    msgendidxplusone += 1
                            if terminated_message or bad_termination:
                                msgendidxplusone += 1
                            if not terminated_message:
                                complete_message = False
                        else:
                            msgendidxplusone = msgstartidx + msgclass._LENGTH

                        if complete_message and not bad_termination and channel_match_orNA:
                            try:
                                msg = msgclass.from_bytes(midibytes[msgstartidx+1:msgendidxplusone])
                            except(ValueError, TypeError) as e:
                                msg = MIDIBadEvent(midibytes[msgstartidx+1:msgendidxplusone], e)                               

                    break  # for

            # break out of while loop for a complete message on good channel
            # or we have one we do not know about
            if known_message:
                if complete_message:
                    if channel_match_orNA:
                        break
                    else:
                        msgstartidx = msgendidxplusone
                else:
                    # Important case of a known message but one that is not
                    # yet complete - leave bytes in buffer and wait for more
                    break
            else:
                msg = MIDIUnknownEvent(status)
                # length cannot be known
                # next read will skip past leftover data bytes
                msgendidxplusone = msgstartidx + 1
                break

        if msg is not None:
            return (msg, startidx, msgendidxplusone, skipped, channel)
        else:
            return (None, startidx, msgendidxplusone, skipped, None)

    # channel value present to keep interface uniform but unused
    def as_bytes(self, channel=None):
        """A default method for constructing wire messages with no data.
        Returns a (mutable) bytearray with just status code in."""
        return bytearray([self._STATUS])

    @classmethod
    def from_bytes(cls, databytes):
        """A default method for constructing message objects with no data.
           Returns the new object."""
        return cls()


# DO NOT try to register these messages
class MIDIUnknownEvent(MIDIMessage):
    _LENGTH = -1

    def __init__(self, status):
        self.status = status

class MIDIBadEvent(MIDIMessage):
    _LENGTH = -1

    def __init__(self, data, exception):
        self.data = bytearray(data)
        self.exception_text = repr(exception)
