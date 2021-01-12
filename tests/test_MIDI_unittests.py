# SPDX-FileCopyrightText: 2019 Kevin J. Walters for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import unittest
from unittest.mock import Mock, MagicMock, call

import random
import os

verbose = int(os.getenv("TESTVERBOSE", "2"))

# adafruit_midi had an import usb_midi
import sys

# sys.modules['usb_midi'] = MagicMock()

# Borrowing the dhalbert/tannewt technique from adafruit/Adafruit_CircuitPython_Motor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Full monty
from adafruit_midi.channel_pressure import ChannelPressure
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend
from adafruit_midi.polyphonic_key_pressure import PolyphonicKeyPressure
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.system_exclusive import SystemExclusive
from adafruit_midi.timing_clock import TimingClock

# Import after messages - opposite to other test file
import adafruit_midi


# For loopback/echo tests
def MIDI_mocked_both_loopback(in_c, out_c):
    usb_data = bytearray()

    def write(buffer, length):
        nonlocal usb_data
        usb_data.extend(buffer[0:length])

    def read(length):
        nonlocal usb_data
        poppedbytes = usb_data[0:length]
        usb_data = usb_data[len(poppedbytes) :]
        return bytes(poppedbytes)

    mockedPortIn = Mock()
    mockedPortIn.read = read
    mockedPortOut = Mock()
    mockedPortOut.write = write
    m = adafruit_midi.MIDI(
        midi_out=mockedPortOut, midi_in=mockedPortIn, out_channel=out_c, in_channel=in_c
    )
    return m


def MIDI_mocked_receive(in_c, data, read_sizes):
    usb_data = bytearray(data)
    chunks = read_sizes
    chunk_idx = 0

    def read(length):
        nonlocal usb_data, chunks, chunk_idx
        # pylint:  disable=no-else-return
        if length != 0 and chunk_idx < len(chunks):
            # min() to ensure we only read what's asked for and present
            poppedbytes = usb_data[0 : min(length, chunks[chunk_idx])]
            usb_data = usb_data[len(poppedbytes) :]
            if length >= chunks[chunk_idx]:
                chunk_idx += 1
            else:
                chunks[chunk_idx] -= len(poppedbytes)
            return bytes(poppedbytes)
        else:
            return bytes()

    mockedPortIn = Mock()
    mockedPortIn.read = read

    m = adafruit_midi.MIDI(
        midi_out=None, midi_in=mockedPortIn, out_channel=in_c, in_channel=in_c
    )
    return m


class Test_MIDI_constructor(unittest.TestCase):
    def test_no_inout(self):
        # constructor likes a bit of in out
        with self.assertRaises(ValueError):
            adafruit_midi.MIDI()


class Test_MIDI(unittest.TestCase):
    # pylint: disable=too-many-branches
    def test_captured_data_one_byte_reads(self):
        c = 0
        # From an M-Audio AXIOM controller
        raw_data = bytearray(
            [0x90, 0x3E, 0x5F]
            + [0xD0, 0x10]
            + [0x90, 0x40, 0x66]
            + [0xB0, 0x1, 0x08]
            + [0x90, 0x41, 0x74]
            + [0xE0, 0x03, 0x40]
        )
        m = MIDI_mocked_receive(c, raw_data, [1] * len(raw_data))

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x3E)
        self.assertEqual(msg.velocity, 0x5F)
        self.assertEqual(msg.channel, c)

        # for loops currently absorb any Nones but could
        # be set to read precisely the expected number...
        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, ChannelPressure)
        self.assertEqual(msg.pressure, 0x10)
        self.assertEqual(msg.channel, c)

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x40)
        self.assertEqual(msg.velocity, 0x66)
        self.assertEqual(msg.channel, c)

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, ControlChange)
        self.assertEqual(msg.control, 0x01)
        self.assertEqual(msg.value, 0x08)
        self.assertEqual(msg.channel, c)

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x41)
        self.assertEqual(msg.velocity, 0x74)
        self.assertEqual(msg.channel, c)

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            if msg is not None:
                break
        self.assertIsInstance(msg, PitchBend)
        self.assertEqual(msg.pitch_bend, 8195)
        self.assertEqual(msg.channel, c)

        for unused in range(100):  # pylint: disable=unused-variable
            msg = m.receive()
            self.assertIsNone(msg)

    def test_unknown_before_NoteOn(self):
        c = 0
        # From an M-Audio AXIOM controller
        raw_data = bytes(
            [0b11110011, 0x10]  # Song Select (not yet implemented)
            + [0b11110011, 0x20]
            + [0b11110100]
            + [0b11110101]
        ) + bytes(NoteOn("C5", 0x7F, channel=c))
        m = MIDI_mocked_receive(c, raw_data, [2, 2, 1, 1, 3])

        for unused in range(4):  # pylint: disable=unused-variable
            msg = m.receive()
            self.assertIsInstance(msg, adafruit_midi.midi_message.MIDIUnknownEvent)
            self.assertIsNone(msg.channel)

        msg = m.receive()
        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x48)  # 0x48 is C5
        self.assertEqual(msg.velocity, 0x7F)
        self.assertEqual(msg.channel, c)

    # See https://github.com/adafruit/Adafruit_CircuitPython_MIDI/issues/8
    def test_running_status_when_implemented(self):
        c = 8
        raw_data = (
            bytes(NoteOn("C5", 0x7F, channel=c))
            + bytes([0xE8, 0x72, 0x40] + [0x6D, 0x40] + [0x05, 0x41])
            + bytes(NoteOn("D5", 0x7F, channel=c))
        )

        m = MIDI_mocked_receive(c, raw_data, [3 + 3 + 2 + 3 + 3])
        self.assertIsInstance(m, adafruit_midi.MIDI)  # silence pylint!
        # self.assertEqual(TOFINISH, WHENIMPLEMENTED)

    def test_somegood_somemissing_databytes(self):
        c = 8
        raw_data = (
            bytes(NoteOn("C5", 0x7F, channel=c))
            + bytes(
                [0xE8, 0x72, 0x40]
                + [0xE8, 0x6D]  # Missing last data byte
                + [0xE8, 0x5, 0x41]
            )
            + bytes(NoteOn("D5", 0x7F, channel=c))
        )
        m = MIDI_mocked_receive(c, raw_data, [3 + 3 + 2 + 3 + 3])

        msg1 = m.receive()
        self.assertIsInstance(msg1, NoteOn)
        self.assertEqual(msg1.note, 72)
        self.assertEqual(msg1.velocity, 0x7F)
        self.assertEqual(msg1.channel, c)

        msg2 = m.receive()
        self.assertIsInstance(msg2, PitchBend)
        self.assertEqual(msg2.pitch_bend, 8306)
        self.assertEqual(msg2.channel, c)

        # The current implementation will read status bytes for data
        # In most cases it would be a faster recovery with fewer messages
        # lost if the next status byte wasn't consumed
        # and parsing restarted from that byte
        msg3 = m.receive()
        self.assertIsInstance(msg3, adafruit_midi.midi_message.MIDIBadEvent)
        self.assertIsInstance(msg3.data, bytes)
        self.assertEqual(msg3.data, bytes([0xE8, 0x6D, 0xE8]))
        self.assertIsNone(msg3.channel)

        # (msg4, channel4) = m.receive()
        # self.assertIsInstance(msg4, PitchBend)
        # self.assertEqual(msg4.pitch_bend, 72)
        # self.assertEqual(channel4, c)

        msg5 = m.receive()
        self.assertIsInstance(msg5, NoteOn)
        self.assertEqual(msg5.note, 74)
        self.assertEqual(msg5.velocity, 0x7F)
        self.assertEqual(msg5.channel, c)

        msg6 = m.receive()
        self.assertIsNone(msg6)

    def test_smallsysex_between_notes(self):
        m = MIDI_mocked_both_loopback(3, 3)

        m.send(
            [
                NoteOn("C4", 0x7F),
                SystemExclusive([0x1F], [1, 2, 3, 4, 5, 6, 7, 8]),
                NoteOff(60, 0x28),
            ]
        )

        msg1 = m.receive()
        self.assertIsInstance(msg1, NoteOn)
        self.assertEqual(msg1.note, 60)
        self.assertEqual(msg1.velocity, 0x7F)
        self.assertEqual(msg1.channel, 3)

        msg2 = m.receive()
        self.assertIsInstance(msg2, SystemExclusive)
        self.assertEqual(msg2.manufacturer_id, bytes([0x1F]))
        self.assertEqual(msg2.data, bytes([1, 2, 3, 4, 5, 6, 7, 8]))
        self.assertEqual(msg2.channel, None)  # SysEx does not have a channel

        msg3 = m.receive()
        self.assertIsInstance(msg3, NoteOff)
        self.assertEqual(msg3.note, 60)
        self.assertEqual(msg3.velocity, 0x28)
        self.assertEqual(msg3.channel, 3)

        msg4 = m.receive()
        self.assertIsNone(msg4)

    def test_smallsysex_bytes_type(self):
        s = SystemExclusive([0x1F], [100, 150, 200])

        self.assertIsInstance(s, SystemExclusive)
        self.assertEqual(s.manufacturer_id, bytes([0x1F]))
        self.assertIsInstance(s.manufacturer_id, bytes)

        # check this really is immutable (pylint also picks this up!)
        with self.assertRaises(TypeError):
            s.data[0] = 0  # pylint: disable=unsupported-assignment-operation

        self.assertEqual(s.data, bytes([100, 150, 200]))
        self.assertIsInstance(s.data, bytes)

    # pylint: disable=too-many-locals
    def test_larger_than_buffer_sysex(self):
        c = 0
        monster_data_len = 500
        raw_data = (
            bytes(NoteOn("C5", 0x7F, channel=c))
            + bytes(
                SystemExclusive([0x02], [d & 0x7F for d in range(monster_data_len)])
            )
            + bytes(NoteOn("D5", 0x7F, channel=c))
        )
        m = MIDI_mocked_receive(c, raw_data, [len(raw_data)])
        buffer_len = m._in_buf_size  # pylint: disable=protected-access
        self.assertTrue(
            monster_data_len > buffer_len,
            "checking our SysEx truly is larger than buffer",
        )

        msg1 = m.receive()
        self.assertIsInstance(msg1, NoteOn)
        self.assertEqual(msg1.note, 72)
        self.assertEqual(msg1.velocity, 0x7F)
        self.assertEqual(msg1.channel, c)

        # (Ab)using python's rounding down for negative division
        # pylint: disable=unused-variable
        for unused in range(-(-(1 + 1 + monster_data_len + 1) // buffer_len) - 1):
            msg2 = m.receive()
            self.assertIsNone(msg2)

        # The current implementation will read SysEx end status byte
        # and report it as an unknown
        msg3 = m.receive()
        self.assertIsInstance(msg3, adafruit_midi.midi_message.MIDIUnknownEvent)
        self.assertEqual(msg3.status, 0xF7)
        self.assertIsNone(msg3.channel)

        # (msg4, channel4) = m.receive()
        # self.assertIsInstance(msg4, PitchBend)
        # self.assertEqual(msg4.pitch_bend, 72)
        # self.assertEqual(channel4, c)

        msg5 = m.receive()
        self.assertIsInstance(msg5, NoteOn)
        self.assertEqual(msg5.note, 74)
        self.assertEqual(msg5.velocity, 0x7F)
        self.assertEqual(msg5.channel, c)

        msg6 = m.receive()
        self.assertIsNone(msg6)


# pylint does not like mock_calls - must be a better way to handle this?
# pylint: disable=no-member
class Test_MIDI_send(unittest.TestCase):
    def test_send_basic_single(self):
        # def printit(buffer, len):
        #    print(buffer[0:len])
        mockedPortOut = Mock()
        # mockedPortOut.write = printit

        m = adafruit_midi.MIDI(midi_out=mockedPortOut, out_channel=2)

        # Test sending some NoteOn and NoteOff to various channels
        nextcall = 0
        m.send(NoteOn(0x60, 0x7F))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x60\x7f", 3)
        )
        nextcall += 1
        m.send(NoteOn(0x64, 0x3F))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x64\x3f", 3)
        )
        nextcall += 1
        m.send(NoteOn(0x67, 0x1F))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x67\x1f", 3)
        )
        nextcall += 1

        m.send(NoteOn(0x60, 0x00))  # Alternative to NoteOff
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x60\x00", 3)
        )
        nextcall += 1
        m.send(NoteOff(0x64, 0x01))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x82\x64\x01", 3)
        )
        nextcall += 1
        m.send(NoteOff(0x67, 0x02))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x82\x67\x02", 3)
        )
        nextcall += 1

        # Setting channel to non default
        m.send(NoteOn(0x6C, 0x7F), channel=9)
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x99\x6c\x7f", 3)
        )
        nextcall += 1

        m.send(NoteOff(0x6C, 0x7F), channel=9)
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x89\x6c\x7f", 3)
        )
        nextcall += 1

    def test_send_badnotes(self):
        mockedPortOut = Mock()

        m = adafruit_midi.MIDI(midi_out=mockedPortOut, out_channel=2)

        # Test sending some NoteOn and NoteOff to various channels
        nextcall = 0
        m.send(NoteOn(60, 0x7F))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x3c\x7f", 3)
        )
        nextcall += 1
        with self.assertRaises(ValueError):
            m.send(NoteOn(64, 0x80))  # Velocity > 127 - illegal value

        with self.assertRaises(ValueError):
            m.send(NoteOn(67, -1))

        # test after exceptions to ensure sending is still ok
        m.send(NoteOn(72, 0x7F))
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall], call(b"\x92\x48\x7f", 3)
        )
        nextcall += 1

    def test_send_basic_sequences(self):
        # def printit(buffer, len):
        #    print(buffer[0:len])
        mockedPortOut = Mock()
        # mockedPortOut.write = printit

        m = adafruit_midi.MIDI(midi_out=mockedPortOut, out_channel=2)

        # Test sending some NoteOn and NoteOff to various channels
        nextcall = 0
        # Test sequences with list syntax and pass a tuple too
        note_list = [NoteOn(0x6C, 0x51), NoteOn(0x70, 0x52), NoteOn(0x73, 0x53)]
        note_tuple = tuple(note_list)
        m.send(note_list, channel=10)
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall],
            call(b"\x9a\x6c\x51\x9a\x70\x52\x9a\x73\x53", 9),
            "The implementation writes in one go, single 9 byte write expected",
        )
        nextcall += 1
        m.send(note_tuple, channel=11)
        self.assertEqual(
            mockedPortOut.write.mock_calls[nextcall],
            call(b"\x9b\x6c\x51\x9b\x70\x52\x9b\x73\x53", 9),
            "The implementation writes in one go, single 9 byte write expected",
        )
        nextcall += 1

    def test_termination_with_random_data(self):
        """Test with a random stream of bytes to ensure that the parsing code
        termates and returns, i.e. does not go into any infinite loops.
        """
        c = 0
        random.seed(303808)
        raw_data = bytearray([random.randint(0, 255) for i in range(50000)])
        m = MIDI_mocked_receive(c, raw_data, [len(raw_data)])

        noinfiniteloops = False
        for unused in range(len(raw_data)):  # pylint: disable=unused-variable
            m.receive()  # not interested in returned tuple

        noinfiniteloops = True  # interested in getting to here
        self.assertTrue(noinfiniteloops)


if __name__ == "__main__":
    unittest.main(verbosity=verbose)
