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

import unittest
from unittest.mock import Mock, MagicMock

import os
verbose = int(os.getenv('TESTVERBOSE',2))

# adafruit_midi has an import usb_midi
import sys
sys.modules['usb_midi'] = MagicMock()

import adafruit_midi


### To incorporate into tests
# This is using running status in a rather sporadic manner
#
# Receiving:  ['0xe0', '0x67', '0x40']
# Receiving:  ['0xe0', '0x72', '0x40']
# Receiving:  ['0x6d', '0x40', '0xe0']
# Receiving:  ['0x5', '0x41', '0xe0']
# Receiving:  ['0x17', '0x41', '0xe0']
# Receiving:  ['0x35', '0x41', '0xe0']
# Receiving:  ['0x40', '0x41', '0xe0']

### TODO - re work these when running status is implemented

class MIDIMessage_from_message_byte_tests(unittest.TestCase):
    def test_NoteOn_basic(self):
        data = bytes([0x90, 0x30, 0x7f])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 0)
        
    def test_NoteOn_awaitingthirdbyte(self):
        data = bytes([0x90, 0x30])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)
        self.assertIsNone(msg)
        self.assertEqual(msgendidxplusone, skipped,
                         "skipped must be 0 as it only indicates bytes before a status byte")
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 0,
                         "msgendidxplusone must be 0 as buffer must be lest as is for more data")
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)
        
    def test_NoteOn_predatajunk(self):
        data = bytes([0x20, 0x64, 0x90, 0x30, 0x32])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x32)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 5)
        self.assertEqual(skipped, 2)
        self.assertEqual(channel, 0)
        
    def test_NoteOn_postNoteOn(self):
        data = bytes([0x90 | 0x08, 0x30, 0x7f, 0x90 | 0x08, 0x37, 0x64])
        ichannel = 8

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 8)

    def test_NoteOn_postpartialNoteOn(self):
        data = bytes([0x90, 0x30, 0x7f, 0x90, 0x37])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 0)
        
    def test_NoteOn_preotherchannel(self):
        data = bytes([0x95, 0x30, 0x7f, 0x93, 0x37, 0x64])
        ichannel = 3

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.NoteOn)
        self.assertEqual(msg.note, 0x37)
        self.assertEqual(msg.velocity, 0x64)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 6)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 3)
        
    def test_NoteOn_partialandpreotherchannel(self):
        data = bytes([0x95, 0x30, 0x7f, 0x93, 0x37])
        ichannel = 3

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsNone(msg)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)

    def test_Unknown_Singlebyte(self):
        data = bytes([0xfd])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.MIDIUnknownEvent)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 1)
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)
        
        
if __name__ == '__main__':
    unittest.main(verbosity=verbose)
