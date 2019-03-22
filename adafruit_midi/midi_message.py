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


def channel_filter(channel, channel_spec):
    if isinstance(channel_spec, int):
        if channel_spec == ALL_CHANNELS:
            return True
        else:
            return channel == channel_spec
    elif isinstance(channel_spec, tuple):
        return channel in channel_spec
    else:
        raise ValueError("Incorrect type for channel_spec")

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
                    complete_message = len(midibytes) - msgstartidx >= msgclass._LENGTH
                    if complete_message:
                        if msgclass._CHANNELMASK is not None:
                            channel = status & msgclass._CHANNELMASK
                            channel_match_orNA = channel_filter(channel, channel_in)
                        if msgclass._LENGTH < 0:
                            # TODO code this properly - THIS IS VARIABLE LENGTH MESSAGE
                            complete_message = False
                            msgendidxplusone = endidx + 1   # TODO NOT CORRECT
                        else:
                            msgendidxplusone = msgstartidx + msgclass._LENGTH
                    
                        if channel_match_orNA:
                            msg = msgclass.from_bytes(midibytes[msgstartidx+1:msgendidxplusone])
                    break  # for

            # break out of while loop if we have a complete message
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
                   
        ### TODO THIS IS NOW BUGGY DUE TO 
                   
        ### TODO correct to handle a buffer with start of big SysEx
        ### TODO correct to handle a buffer in middle of big SysEx
        ### TODO correct to handle a buffer with end portion of big SysEx
        if msg is not None:
            return (msg, startidx, msgendidxplusone, skipped, channel)
        else:
            return (None, startidx, msgendidxplusone, skipped, None)

    @classmethod
    def from_bytes(cls, databytes):
        """A default method for constructing messages that have no data.
           Returns the new object."""
        return cls()


# DO NOT try to register this message
class MIDIUnknownEvent(MIDIMessage):
    _LENGTH = -1
    
    def __init__(self, status):
        self.status = status
