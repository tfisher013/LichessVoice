import wave
import struct
import math
import numpy as np
import matplotlib.pyplot as plt
import speech_recognition as sr
import sys
from pydub import AudioSegment
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1 if sys.platform == 'darwin' else 2
RATE = 44100
RECORD_SECONDS = 5

ambient_noise_level = 0
recording_file_path = 'command_recording_file.wav'
end_partition = 7
r = sr.Recognizer()

def trim_audio_file(file_path: str, sound_start_index: float, sound_end_index: float):
    """
    Trims portions of an audio file from the start and end as indicated by the provided
    parameters.

    Parameters
        file_path (str): the path to the audio file to be trimmed.]
        sound_start_index (float): a value in [0.0, 1.0] representing the fraction of the
            file to be trimmed from the start
        sound_end_index (float): a value in [0.0, 1.0] representing the fraction of the
            file to be trimmed from the end
    """

    audio = AudioSegment.from_file(file_path)

    # get total duration of audio file
    total_duration = len(audio)

    # trim audio file and export
    audio = audio[(int)(sound_start_index * total_duration):-(int)(total_duration * (1 - sound_end_index))]
    audio.export(file_path, format='wav')

def rms(data: bytes) -> float:
    """
    Returns a numerical representation of the volume of the provided sound data.

    Parameters
        data (bytes): a byte representation of audio data

    Returns
        float: a numerical representation of the volume of the provided audio data
    """

    count = len(data)/2
    format = '%dh'%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768)
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

def convert_audio_file_to_text(file_path: str) -> str:
    """
    Uses a voice recognition engine to print a text represtation of the speech
    in the provided audio file.

    Parameters
        file_path (str): the path of the file from which to generate text

    Returns
        str: a text representation of the provided audio file, or an error message
            if the interpretation was unsuccessful
    """

    move_file=sr.AudioFile(recording_file_path)
    with move_file as source:
        audio = r.record(source)
        try:
            return  r.recognize_google(audio)
        except Exception as e:
            return 'Error identifying speech. Please try again.'

def start_speech_to_text():
    """
    Begins the routine which listens for voice commands and prints
    the interpreted value to the command line.
    """
    
    num_outer_iter = 0
    while True:
        convert_audio = False
        with wave.open(recording_file_path, 'w') as wf:
            p = pyaudio.PyAudio()
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)

            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

            vol_list = []
            num_samples = RATE // CHUNK * RECORD_SECONDS

            num_inner_iter = 0
            actual_samples = 0
            while True:

                # the first time this method is called, dedicate the recording to determining the
                # level of ambient noise to use as a benchmark when actually identifying speech
                if num_outer_iter == 0:
                    print('Detecting ambient noise level. Please remain silent...')
                else:
                    print('Recording...')

                # save a number of samples of microphone data to file
                for _ in range(0, (int)(num_samples / (num_inner_iter + 1))):
                    sound_data = stream.read(CHUNK, exception_on_overflow = False)
                    vol_list.append(rms(sound_data))
                    wf.writeframes(sound_data)
                    actual_samples += 1

                # restart outer loop after updating ambient noise var on first iteration only
                if num_outer_iter == 0:
                    ambient_noise_level = sum(vol_list) / len(vol_list)
                    print('Ambient noise level: ', ambient_noise_level)
                    break

                # experimentally determined sound thresholds; threshold for identifying the start of
                # an utterance needs to be higher than that denoting the end of one
                start_speech_threshold = 1.25 * ambient_noise_level
                end_speech_threshold = 1.05 * ambient_noise_level
                silence_threshold = 1.5 * ambient_noise_level

                max_val = max(vol_list)
                min_val = min(vol_list)
                # case 1: audio looks to contain sound
                if max_val >= silence_threshold:

                    print('Detected sound in file, silence threshold is ', silence_threshold, ' for min: ', min_val, ', max: ', max_val)

                    # check whether sound in file is isolated (extends to to end of file or not)
                    is_sound_isolated = True
                    end_check_index = round((actual_samples * (1.0 - (1.0 / end_partition))))
                    num_matches = 0
                    for i in range(end_check_index, actual_samples):
                        if vol_list[i] > start_speech_threshold:
                            num_matches += 1

                            # if we find a certain number of samples above a certain threshold
                            # in the last 1/end_partition samples, consider the sound to be not
                            # isolated
                            if num_matches > 3:
                                is_sound_isolated = False
                                break

                    # case 2: sound within sample is isolated -> convert to text
                    if is_sound_isolated:      
                        print('--> Sound is isolated')
                        convert_audio = True

                        # could we parallelize the two checks below with threads?

                        start_silence_index = 0
                        end_silence_index = num_samples
                        sound_start_threshold = 5
                        # find starting index of sound from the start
                        count = 0
                        for i in range(0, num_samples):
                            if vol_list[i] >= start_speech_threshold:
                                count += 1
                                if count == sound_start_threshold:
                                    start_silence_index = max(0, i - 2 * count)
                                    break
                        # find starting index of sound from the end
                        count = 0
                        for i in reversed(range(0, num_samples)):
                            if vol_list[i] >= end_speech_threshold:
                                count += 1
                                if count == sound_start_threshold:
                                    end_silence_index = min(i + 6 * count, actual_samples)
                                    break

                        # remove silence at beginning and end of file
                        trim_audio_file(recording_file_path, start_silence_index / actual_samples, end_silence_index / actual_samples)

                        break

                    # case 3: sound within sample is not isolated -> record for additional time to capture entire command
                    else:
                        num_inner_iter += 1
                        print('--> Sound is not isolated, recording for additional ', RECORD_SECONDS / (num_inner_iter + 1), 'seconds.')
                        continue
                
                # case 4: audio contains no sound -> overwrite file
                else:
                    print('Detected no sound in file')
                    break

            # close file being written to once we have isolated sound
            stream.close()
            p.terminate()

            if convert_audio:
                convert_audio = False
                move_text = convert_audio_file_to_text(recording_file_path)
                print(move_text)

            num_outer_iter += 1


if __name__ == "__main__":
    """
    Main method for testing
    """

    start_speech_to_text()

