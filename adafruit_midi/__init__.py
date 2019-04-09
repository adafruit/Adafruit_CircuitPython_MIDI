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

from .midi_message import MIDIMessage, ALL_CHANNELS

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MIDI.git"


class MIDI:
    """MIDI helper class. ``midi_in`` or ``midi_out`` *must* be set or both together.

    :param midi_in: an object which implements ``read(length)``,
        set to ``usb_midi.ports[0]`` for USB MIDI, default None.
    :param midi_out: an object which implements ``write(buffer, length)``,
        set to ``usb_midi.ports[1]`` for USB MIDI, default None.
    :param in_channel: The input channel(s).
        This is used by ``receive`` to filter data.
        This can either be an ``int`` for the wire protocol channel number (0-15)
        a tuple of ``int`` to listen for multiple channels or ``"ALL"``.
        Defaults to None.
    :param int out_channel: The wire protocol output channel number (0-15)
        used by ``send`` if no channel is specified,
        defaults to 0 (MIDI Channel 1).
    :param int in_buf_size: Maximum size of input buffer in bytes, default 30.
    :param bool debug: Debug mode, default False.

    """

    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    PITCH_BEND = 0xE0
    CONTROL_CHANGE = 0xB0

    def __init__(self, midi_in=None, midi_out=None, *,
                 in_channel=None, out_channel=0, in_buf_size=30, debug=False):
        if midi_in is None and midi_out is None:
            raise ValueError("No midi_in or midi_out provided")
        self._midi_in = midi_in
        self._midi_out = midi_out
        self._in_channel = in_channel  # dealing with pylint inadequacy
        self.in_channel = in_channel
        self._out_channel = out_channel  # dealing with pylint inadequacy
        self.out_channel = out_channel
        self._debug = debug
        # This input buffer holds what has been read from midi_in
        self._in_buf = bytearray(0)
        self._in_buf_size = in_buf_size
        self._outbuf = bytearray(4)
        self._skipped_bytes = 0

    @property
    def in_channel(self):
        """The incoming MIDI channel. Must be 0-15. Correlates to MIDI channels 1-16, e.g.
        ``in_channel = 3`` will listen on MIDI channel 4.
        Can also listen on multiple channels, e.g. ``in_channel  = (0,1,2)``
        will listen on MIDI channels 1-3 or ``in_channel = "ALL"`` for every channel.
        Default is None."""
        return self._in_channel

    @in_channel.setter
    def in_channel(self, channel):
        if channel is None or (isinstance(channel, int) and 0 <= channel <= 15):
            self._in_channel = channel
        elif isinstance(channel, str) and channel == "ALL":
            self._in_channel = ALL_CHANNELS
        elif isinstance(channel, tuple) and all(0 <= c <= 15 for c in channel):
            self._in_channel = channel
        else:
            raise RuntimeError("Invalid input channel")

    @property
    def out_channel(self):
        """The outgoing MIDI channel. Must be 0-15. Correlates to MIDI channels 1-16, e.g.
        ``out_channel = 3`` will send to MIDI channel 4. Default is 0 (MIDI channel 1)."""
        return self._out_channel

    @out_channel.setter
    def out_channel(self, channel):
        if not 0 <= channel <= 15:
            raise RuntimeError("Invalid output channel")
        self._out_channel = channel

    def receive(self):
        """Read messages from MIDI port, store them in internal read buffer, then parse that data
        and return the first MIDI message (event).
        This maintains the blocking characteristics of the midi_in port.

        :returns MIDIMessage object: Returns object or None for nothing.
        """
        ### could check _midi_in is an object OR correct object OR correct interface here?
        # If the buffer here is not full then read as much as we can fit from
        # the input port
        if len(self._in_buf) < self._in_buf_size:
            bytes_in = self._midi_in.read(self._in_buf_size - len(self._in_buf))
            if bytes_in:
                if self._debug:
                    print("Receiving: ", [hex(i) for i in bytes_in])
                self._in_buf.extend(bytes_in)
                del bytes_in

        (msg, endplusone,
         skipped) = MIDIMessage.from_message_bytes(self._in_buf, self._in_channel)
        if endplusone != 0:
            # This is not particularly efficient as it's copying most of bytearray
            # and deleting old one
            self._in_buf = self._in_buf[endplusone:]

        self._skipped_bytes += skipped

        # msg could still be None at this point, e.g. in middle of monster SysEx
        return msg

    def send(self, msg, channel=None):
        """Sends a MIDI message.

        :param msg: Either a MIDIMessage object or a sequence (list) of MIDIMessage objects.
            The channel property will be *updated* as a side-effect of sending message(s).
        :param int channel: Channel number, if not set the ``out_channel`` will be used.

        """
        if channel is None:
            channel = self.out_channel
        if isinstance(msg, MIDIMessage):
            msg.channel = channel
            data = msg.__bytes__()  # bytes(object) does not work in uPy
        else:
            data = bytearray()
            for each_msg in msg:
                each_msg.channel = channel
                data.extend(each_msg.__bytes__())

        self._send(data, len(data))

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

        :param int control: The controller number. Must be 0-127.
        :param int value: The control value. Must be 0-127.

        """
        self._generic_3(self.CONTROL_CHANGE, control, value, channel)

    def _generic_3(self, cmd, arg1, arg2, channel=None):
        if not 0 <= arg1 <= 0x7F:
            raise RuntimeError("Argument 1 value %d invalid" % arg1)
        if not 0 <= arg2 <= 0x7F:
            raise RuntimeError("Argument 2 value %d invalid" % arg2)
        if channel is None:
            channel = self._out_channel
        self._outbuf[0] = (cmd & 0xF0) | (channel & 0x0f)
        self._outbuf[1] = arg1
        self._outbuf[2] = arg2
        self._send(self._outbuf, 3)

    def _send(self, packet, num):
        if self._debug:
            print("Sending: ", [hex(i) for i in packet[:num]])
        self._midi_out.write(packet, num)
