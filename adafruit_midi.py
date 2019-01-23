class MIDI:
    """A helper for encoding/decoding MIDI packets over a midi or uart connection"""

    NOTE_ON = 0x90
    NOTE_OFF = 0x80

    def __init__(self, midi_in, midi_out, *, in_channel=None, out_channel=0):
        self._midi_in = midi_in
        self._midi_out = midi_out
        self.in_channel = in_channel
        self.out_channel = out_channel
        self._debug = True

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
        if not (0 <= note <= 0x7F):
            raise RuntimeError("Note value invalid")
        if not (0 <= vel <= 0x7F):
            raise RuntimeError("Velocity invalid")
        if not channel:
            channel = self._out_channel
        self._send([self.NOTE_ON | channel, note, vel])

    def _send(self, packet):
        if self._debug:
            print("Sending: ", [hex(i) for i in packet])
        print(self._midi_out(packet))
