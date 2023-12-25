import wave
import struct
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import speech_recognition as sr

import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1 if sys.platform == 'darwin' else 2
RATE = 44100
RECORD_SECONDS = 5

end_partition = 5
figure_counter = 1
r = sr.Recognizer()

def rms( data ):
    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768)
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

num_outer_iter = 0
while num_outer_iter < 1:
    convert_audio = False
    with wave.open('output.wav', 'w') as wf:
        p = pyaudio.PyAudio()
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

        vol_list = []
        num_samples = RATE // CHUNK * RECORD_SECONDS
        print('Recording...')

        num_inner_iter = 0
        while True:
            for _ in range(0, num_samples):
                sound_data = stream.read(CHUNK, exception_on_overflow = False)
                vol_list.append(rms(sound_data))
                wf.writeframes(sound_data)
            print('Done')

            # decide what to do based on sound in file
            max_val = max(vol_list)
            min_val = min(vol_list)
            silence_threshold = 0.3 * max_val
            # case 1: audio looks to contain sound
            if (max_val / min_val) / max_val >= 0.3:

                print("Detected sound in file, silence threshold is "+str(silence_threshold))

                # case 2: sound within sample is isolated --> BEGIN BY TESTING THIS CASE
                end_check_index = round((num_samples * (1.0 - (1.0 / end_partition))))
                end_check_len = round((num_samples * (1.0 / end_partition)))
                print("Average of last fifth of values is "+str(sum(vol_list[end_check_index:]) / end_check_len))
                if sum(vol_list[end_check_index:]) / end_check_len <= silence_threshold:      
                    print('--> Sound is isolated')
                    convert_audio = True

                    plt.figure(figure_counter)
                    plt.plot(vol_list)
                    plt.title('Original Signal')
                    figure_counter += 1

                    # could we parallelize the two checks with threads below?

                    start_silence_index = 0
                    end_silence_index = num_samples - 1
                    sound_start_threshold = 5
                    # find starting index of sound from the start
                    count = 0
                    for i in range(0, num_samples):
                        if vol_list[i] >= silence_threshold:
                            count += 1
                            if count == sound_start_threshold:
                                start_silence_index = i - count
                                break
                    # find starting index of sound from the end
                    print('Start isolation index = '+str(start_silence_index))
                    count = 0
                    for i in reversed(range(0, num_samples)):
                        if vol_list[i] >= silence_threshold:
                            count += 1
                            if count == sound_start_threshold:
                                end_silence_index = i + count
                                break
                    print('End isolation index = '+str(end_silence_index))

                    # remove silent sections from start
                    vol_list = [ele for idx, ele in enumerate(vol_list) if idx not in range(end_silence_index, num_samples - 1)]

                    # remove silent sections from start
                    vol_list = [ele for idx, ele in enumerate(vol_list) if idx not in range(0, start_silence_index)]

                    # process sound
                    plt.figure(figure_counter)
                    plt.plot(vol_list)
                    plt.title('Truncated Signal')
                    figure_counter += 1

                    break

                # case 3: sound within sample is not isolated
                else:
                    print('--> Sound is not isolated')
                    num_inner_iter += 1
                    continue
            
            # case 4: audio contains no sound (do nothing, continue to next loop iteration)
            else:
                print("Detected no sound in file")
                break

        stream.close()
        p.terminate()

        if convert_audio:
            print("Converting audio...")
            convert_audio = False
            hellow=sr.AudioFile('output.wav')
            with hellow as source:
                audio = r.record(source)
                try:
                    s = r.recognize_google(audio)
                    print("Text: "+s)
                except Exception as e:
                    print("Exception: "+str(e))

        num_outer_iter += 1

        # plt.plot(vol_list)
        plt.show()