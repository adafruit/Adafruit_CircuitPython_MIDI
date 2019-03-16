# The MIT License (MIT)
#
# Copyright (c) 2019 Limor Fried for Adafruit Industries, Kevin J. Walters
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


* Author(s): Limor Fried, Kevin J. Walters

Implementation Notes
--------------------

**Hardware:**



**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import usb_midi

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


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

    @classmethod
    def from_message_bytes(cls, midibytes):
        """Create an appropriate object of the correct class for the first message found in
           some MIDI bytes.
           Returns (messageobject, start, endplusone) or None for no message or partial message.
        """

        msg = None
        startidx = 0
        endidx = len(midibytes) - 1

        # Look for a status byte
        # Second rule of the MIDI club is status bytes have MSB set
        while startidx <= endidx and not (midibytes[startidx] & 0x80):
            startidx += 1
        
        # Either no message or a partial one
        if startidx > endidx:
            return None

        status = midibytes[startidx]
        msgendidx = -1
        smfound = False
        # Rummage through our list looking for a status match
        for sm, msgclass in MIDIMessage._statusandmask_to_class:
            maskedstatus = status & sm[1]
            if sm[0] == maskedstatus:
                smfound = True
                # Check there's enough left to parse a complete message
                if len(midibytes) - startidx >= msgclass._LENGTH:
                    if msgclass._LENGTH < 0:
                        # TODO code this properly
                        msgendidxplusone = endidx + 1   # TODO NOT CORRECT
                    else:
                        msgendidxplusone = startidx + msgclass._LENGTH
                    msg = msgclass.from_bytes(midibytes[startidx+1:msgendidxplusone])
                break
        
        if not smfound:
            msg = MIDIUnknownEvent(status)
            # length cannot be known
            # next read will skip past leftover data bytes
            msgendidxplusone = startidx + 1
            
        ### TODO correct to handle a buffer with start of big SysEx
        ### TODO correct to handle a buffer in middle of big SysEx
        ### TODO correct to handle a buffer with end portion of big SysEx
        if msg is not None:
            return (msg, startidx, msgendidxplusone)
        else:
            return None

            
    @classmethod
    def from_bytes(cls, databytes):
        """A default method for constructing messages that have no data.
           Returns the new object."""
        return cls()
            

class Start(MIDIMessage):
    _STATUS = 0xfa
    _STATUSMASK = 0xff
    _LENGTH = 1

Start.register_message_type()


class Stop(MIDIMessage):
    _STATUS = 0xfc
    _STATUSMASK = 0xff
    _LENGTH = 1

Stop.register_message_type()


# Would be good to have this registered first as it occurs
# frequently when in-use
class TimingClock(MIDIMessage):
    _STATUS = 0xf8
    _STATUSMASK = 0xff
    _LENGTH = 1

TimingClock.register_message_type()


class NoteOff(MIDIMessage):
    _STATUS = 0x80
    _STATUSMASK = 0xf0
    _LENGTH = 3
    
    def __init__(self, note, vel):
        self.note = note
        self.vel = vel
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0], databytes[1])  
        
NoteOff.register_message_type()


class NoteOn(MIDIMessage):
    _STATUS = 0x90
    _STATUSMASK = 0xf0
    _LENGTH = 3
    
    def __init__(self, note, vel):
        self.note = note
        self.vel = vel
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0], databytes[1])  
   
NoteOn.register_message_type()


class PolyphonicKeyPressure(MIDIMessage):
    _STATUS = 0xa0
    _STATUSMASK = 0xf0
    _LENGTH = 3
    
    def __init__(self, note, pressure):
        self.note = note
        self.pressure = pressure
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0], databytes[1])  
        
PolyphonicKeyPressure.register_message_type()


class ControlChange(MIDIMessage):
    _STATUS = 0xb0
    _STATUSMASK = 0xf0
    _LENGTH = 3
    
    def __init__(self, control, value):
        self.control = control
        self.value = value
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0], databytes[1])  
        
ControlChange.register_message_type()


class ProgramChange(MIDIMessage):
    _STATUS = 0xc0
    _STATUSMASK = 0xf0
    _LENGTH = 2
    
    def __init__(self, patch):
        self.patch = patch
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0])  

ProgramChange.register_message_type()


class ChannelPressure(MIDIMessage):
    _STATUS = 0xd0
    _STATUSMASK = 0xf0
    _LENGTH = 2
    
    def __init__(self, pressure):
        self.pressure = pressure
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[0])  

ChannelPressure.register_message_type()


class PitchBendChange(MIDIMessage):
    _STATUS = 0xe0
    _STATUSMASK = 0xf0
    _LENGTH = 3
    
    def __init__(self, value):
        self.value = value
    
    @classmethod
    def from_bytes(cls, databytes):
        return cls(databytes[1] << 7 | databytes[0])  

PitchBendChange.register_message_type()


# DO NOT try to register this message
class MIDIUnknownEvent(MIDIMessage):
    _LENGTH = -1
    
    def __init__(self, status):
        self.status = status


class MIDI:
    """MIDI helper class."""

    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    PITCH_BEND = 0xE0
    CONTROL_CHANGE = 0xB0

    ALL_CHANNELS = -1
    
    def __init__(self, midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], *, in_channel=None,
                 out_channel=0, debug=False, in_buf_size=30):
        self._midi_in = midi_in
        self._midi_out = midi_out
        self.in_channel = in_channel
        self.out_channel = out_channel
        self._debug = debug
        # This input buffer holds what has been read from midi_in
        self._inbuf = bytearray(0)
        self._inbuf_size = in_buf_size
        self._outbuf = bytearray(4)

    @property
    def in_channel(self):
        """The incoming MIDI channel. Must be 0-15. Correlates to MIDI channels 1-16, e.g.
        ``in_channel(3)`` will listen on MIDI channel 4. Default is 0."""
        return self._in_channel

    @in_channel.setter
    def in_channel(self, channel):
        if channel is None or (isinstance(channel, int) and 0 <= channel <= 15):
            self._in_channel = channel
        elif isinstance(channel, str) and channel == "ALL":
            self._in_channel = self.ALL_CHANNELS
        elif isinstance(channel, tuple) and all(0 <= c <= 15 for c in channel):
            self._in_channel = channel
        else:
            raise RuntimeError("Invalid input channel")

    @property
    def out_channel(self):
        """The outgoing MIDI channel. Must be 0-15. Correlates to MIDI channels 1-16, e.g.
        ``out_channel(3)`` will send to MIDI channel 4. Default is 0."""
        return self._out_channel

    @out_channel.setter
    def out_channel(self, channel):
        if not 0 <= channel <= 15:
            raise RuntimeError("Invalid output channel")
        self._out_channel = channel

    ### TODO - consider naming here and channel selection and omni mode
    def read_in_port(self):
        ### could check _midi_in is an object OR correct object OR correct interface here?
        # If the buffer here is not full then read as much as we can fit from
        # the input port
        if len(self._inbuf) < self._inbuf_size:
            self._inbuf.extend(self._midi_in.read(self._inbuf_size - len(self._inbuf)))
 
        # TODO - VERY IMPORTANT - WORK OUT HOW TO HANDLE CHANNEL FILTERING
        # AND THINK ABOUT OMNI MODE
        
        ### TODO need to ensure code skips past unknown data/messages in buffer
        ### aftertouch from Axiom 25 causes 6 in the buffer!!
        msgse = MIDIMessage.from_message_bytes(self._inbuf)
        if msgse is not None:
            (msg, start, endplusone) = msgse
            # This is not particularly efficient as it's copying most of bytearray
            # and deleting old one
            self._inbuf = self._inbuf[endplusone:]
            # msg could still be None at this point, e.g. in middle of monster SysEx
            return msg
        else:
            return None


    def note_on(self, note, vel, channel=None):
        """Sends a MIDI Note On message.

        :param int note: The note number. Must be 0-127.
        :param int vel: The note velocity. Must be 0-127.

        """
        self._generic_3(self.NOTE_ON, note, vel, channel)

    def note_off(self, note, vel, channel=None):
        """Sends a MIDI Note Off message.

        :param int note: The note number. Must be 0-127.
        :param int vel: The note velocity. Must be 0-127.

        """
        self._generic_3(self.NOTE_OFF, note, vel, channel)

    def pitch_bend(self, value, channel=None):
        """Send a MIDI Pitch Wheel message.

        :param int value: Range is 0-16383. A ``value`` of 8192 equates to no pitch bend, a value
                          of less than 8192 equates to a negative pitch bend, and a value of more
                          than 8192 equates to a positive pitch bend.

        """
        self._generic_3(self.PITCH_BEND, value & 0x7F, value >> 7, channel)

    def control_change(self, control, value, channel=None):
        """Sends a MIDI CC message.

        :param int control: The controller number. Must be 0-15.
        :param int value: The control value. Must be 0-127.

        """
        self._generic_3(self.CONTROL_CHANGE, control, value, channel)

    def _generic_3(self, cmd, arg1, arg2, channel=None):
        if not 0 <= arg1 <= 0x7F:
            raise RuntimeError("Argument 1 value %d invalid" % arg1)
        if not 0 <= arg2 <= 0x7F:
            raise RuntimeError("Argument 2 value %d invalid" % arg2)
        ### TODO - change this to use is operator and range check or mask it
        if not channel:
            channel = self._out_channel
        self._outbuf[0] = (cmd & 0xF0) | channel
        self._outbuf[1] = arg1
        self._outbuf[2] = arg2
        self._send(self._outbuf, 3)

    def _send(self, packet, num):
        if self._debug:
            print("Sending: ", [hex(i) for i in packet[:num]])
        self._midi_out.write(packet, num)
