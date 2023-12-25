import pyttsx3
import os.path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from pydub import AudioSegment

def change_pitch(input_file, output_file, semitones):
    # Load the audio file
    audio = AudioSegment.from_file(input_file, format="wav")

    # Change the pitch
    audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * (2 ** (semitones / 12.0)))
    })

    # Export the modified audio to a new file
    audio.export(output_file, format="wav")


engine = pyttsx3.init()
voices = engine.getProperty('voices')
rates: [int] = list(range(200, 301, 10))
pitches: [int] = list(range(-4, 5, 1))

for voice in voices:
	for rate in rates:
		for pitch in pitches:
			engine.setProperty('voice', voice.id)
			engine.setProperty('rate', rate)

			file_name = os.path.basename(voice.id)
			file_name += '-rate-' + str(rate)
			file_name += '-pitch-' + str(pitch)
			file_name += '.wav'
			file_name = os.path.join('samples', file_name)

			engine.save_to_file("Hello World!", file_name)

			engine.runAndWait()

			change_pitch(file_name, file_name, pitch)