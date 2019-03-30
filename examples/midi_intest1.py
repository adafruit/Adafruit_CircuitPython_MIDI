import time
import random
import adafruit_midi

### 0 is MIDI channel 1
midi = adafruit_midi.MIDI(in_channel=0)

print("Midi test II")

# Convert channel numbers at the presentation layer to the ones musicians use
print("Input channel:", midi.in_channel + 1 )
print("Listening on input channel:", midi.in_channel + 1)

# play with the pause to simulate code doing other stuff
# in the loop
pauses = [0] * 10 + [.010] * 10 + [0.100] * 10 + [1.0] * 10

while True:
    for pause in pauses:
        msg = midi.receive()
        if msg is not None:
            print(time.monotonic(), msg)
        if pause:
            time.sleep(pause)
