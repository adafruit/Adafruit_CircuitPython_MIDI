Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-midi/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/midi/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_MIDI/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_MIDI/actions/
    :alt: Build Status

A CircuitPython helper for encoding/decoding MIDI packets over a MIDI or UART connection.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
--------------------

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-midi/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-midi

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-midi

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-midi

Usage Example
=============

.. code-block:: python

    import time
    import random
    import usb_midi
    import adafruit_midi

    from adafruit_midi.note_on import NoteOn
    from adafruit_midi.note_off import NoteOff
    from adafruit_midi.pitch_bend import PitchBend
    from adafruit_midi.control_change import ControlChange

    midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

    print("Midi test")

    print("Default output MIDI channel:", midi.out_channel + 1)

    while True:
        midi.send(NoteOn(44, 120))  # G sharp 2nd octave
        time.sleep(0.25)
        a_pitch_bend = PitchBend(random.randint(0, 16383))
        midi.send(a_pitch_bend)
        time.sleep(0.25)
        midi.send([NoteOff("G#2", 120),
                   ControlChange(3, 44)])
        time.sleep(0.5)


Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/midi/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_MIDI/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
