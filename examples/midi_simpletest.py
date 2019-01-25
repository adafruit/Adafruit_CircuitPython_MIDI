import time
import random
import adafruit_midi

midi = adafruit_midi.MIDI(out_channel=0)

print("Midi test")

print("Default output channel:", midi.out_channel)
print("Listening on input channel:", midi.in_channel)

while True:
    midi.note_on(44, 120)
    midi.note_off(44, 120)
    midi.control_change(3, 44)
    midi.pitch_bend(random.randint(0, 16383))
    time.sleep(1)
