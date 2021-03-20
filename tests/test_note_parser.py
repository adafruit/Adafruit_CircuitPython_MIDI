# SPDX-FileCopyrightText: 2019 Kevin J. Walters for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import unittest

import os

verbose = int(os.getenv("TESTVERBOSE", "2"))

# pylint: disable=wrong-import-position
# adafruit_midi had an import usb_midi
import sys

# sys.modules['usb_midi'] = MagicMock()

# Borrowing the dhalbert/tannewt technique from adafruit/Adafruit_CircuitPython_Motor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adafruit_midi.midi_message import note_parser

# pylint: enable=wrong-import-position


class Test_note_parser(unittest.TestCase):
    def text_int_passthru(self):
        self.assertEqual(note_parser(0), 0)
        self.assertEqual(note_parser(70), 70)
        self.assertEqual(note_parser(127), 127)

        # it does not range check so these should pass
        self.assertEqual(note_parser(-303), -303)
        self.assertEqual(note_parser(808), 808)

    def test_good_text(self):
        note_prefix = {
            "Cb": 11,
            "C": 12,
            "C#": 13,
            "Db": 13,
            "D": 14,
            "D#": 15,
            "Eb": 15,
            "E": 16,
            "Fb": 16,
            "E#": 17,
            "F": 17,
            "F#": 18,
            "Gb": 18,
            "G": 19,
            "G#": 20,
            "Ab": 20,
            "A": 21,
            "A#": 22,
            "Bb": 22,
            "B": 23,
            "B#": 24,
        }

        # test from Cb0 to B#8
        for prefix, base_value in note_prefix.items():
            for octave in range(9):
                note = prefix + str(octave)
                expected_value = base_value + octave * 12  # 12 semitones in octave
                self.assertEqual(note_parser(note), expected_value)

        # re-test with simple C4/A4 tests to catch any bugs in above
        self.assertEqual(note_parser("C4"), 60)
        self.assertEqual(note_parser("A4"), 69)

    def test_bad_text(self):

        for text_note in ["H", "H4", "asdfasdfasdf", "000", "999"]:
            with self.assertRaises(ValueError):
                note_parser(text_note)


if __name__ == "__main__":
    unittest.main(verbosity=verbose)
