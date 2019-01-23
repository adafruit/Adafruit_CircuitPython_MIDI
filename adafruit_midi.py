class MIDI:
    """A helper for encoding/decoding MIDI packets over a midi or uart connection"""

    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    PITCH_BEND = 0xE0
    CONTROL_CHANGE = 0xB0

    def __init__(self, midi_in, midi_out, *, in_channel=None, out_channel=0):
        self._midi_in = midi_in
        self._midi_out = midi_out
        self.in_channel = in_channel
        self.out_channel = out_channel
        self._debug = True
        self._outbuf = bytearray(4)

    @property
    def in_channel(self):
        return self._in_channel

    @in_channel.setter
    def in_channel(self, channel):
        if (channel is not None) and not (0 <= channel <= 15):
            raise RuntimeError("Invalid input channel")
        self._in_channel = channel

    @property
    def out_channel(self):
        return self._out_channel

    @out_channel.setter
    def out_channel(self, channel):
        if not (0 <= channel <= 15):
            raise RuntimeError("Invalid output channel")
        self._out_channel = channel

    def note_on(self, note, vel, channel=None):
        self._generic_3(self.NOTE_ON, note, vel, channel)

    def note_off(self, note, vel, channel=None):
        self._generic_3(self.NOTE_OFF, note, vel, channel)

    def pitch_bend(self, value, channel=None):
        self._generic_3(self.PITCH_BEND, value & 0x7F, value >> 7, channel)

    def control_change(self, control, value, channel=None):
        self._generic_3(self.CONTROL_CHANGE, control, value, channel)

    def _generic_3(self, cmd, arg1, arg2, channel=None):
        if not (0 <= arg1 <= 0x7F):
            raise RuntimeError("Argument 1 value %d invalid" % arg1)
        if not (0 <= arg2 <= 0x7F):
            raise RuntimeError("Argument 2 value %d invalid" % arg2)
        if not channel:
            channel = self._out_channel
        self._outbuf[0] = (cmd & 0xF0) | channel
        self._outbuf[1] = arg1
        self._outbuf[2] = arg2
        self._send(self._outbuf, 3)

    def _send(self, packet, num):
        if self._debug:
            print("Sending: ", [hex(i) for i in packet[:num]])
        print(self._midi_out.write(packet, num))
