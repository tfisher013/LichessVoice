from contextlib import closing
import os
import time
from typing import List
import sys
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from gtts import gTTS
from pydub import AudioSegment
import pyttsx3
from text_move_enumerator import *

move_files_directory: str = 'move_files'
all_text_moves = get_all_text_moves()
all_voice_moves = get_all_voice_moves()

def change_pitch(input_file, output_file, semitones):
    """
    Changes the pitch of the provided audio file by the
    number of provided semitones.
    
    Parameters
        input_file (str): the os.path to the audio file to read in
        output_file (str): the os.path of the file to which the
            audio should be written.
        semitones (int): the number of semitones by which the
            pitch of the input file should be changed.    
    """
    # Load the audio file
    audio = AudioSegment.from_file(input_file, format="wav")

    # Change the pitch
    audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * (2 ** (semitones / 12.0)))
    })

    # Export the modified audio to a new file
    audio.export(output_file, format="wav")

def generate_gtts_files():
    """
    Generates and saves audio files for all enumerated chess moves
    using the gTTS engine. Parameters of the engine are varied to
    produce the maximum number files per move possible.
    """

    # -- Speech Parameters for gTTS --
    # top level domains, which result in different accents
    tlds: List[str] = ['com.au', 'us', 'co.in', 'ie']
    speeds: List[bool] = [True, False]

    for move_index in range(0, len(all_voice_moves)):
        move = all_voice_moves[move_index]
        for speed in speeds:
            for tld in tlds:

                tts = gTTS(move, lang='en', tld=tld, slow=speed, lang_check=True)

                file_name = move + '-' +str(uuid.uuid1().fields[0])
                file_name = os.path.join(move_files_directory, all_text_moves[move_index], file_name)
                tts.save(file_name + '.mp3')

                # gTTS only saves as mp3, so convert to wav afterwards
                sound = AudioSegment.from_mp3(file_name)
                sound.export(os.path.basename(file_name) + '.wav', format='wav')

        # gTTS has a usage quota currently set at 900 reqs/min
        # (https://cloud.google.com/speech-to-text/quotas)
        # Adding brief pauses to avoid exceeding this limit
        time.sleep(1.0)

def generate_pyttsx3_files():
    """
    Generates and saves audio files for all enumerated chess moves
    using the pyttsx3 engine. Parameters of the engine are varied to
    produce a large number files per move.
    """

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    rates: List[int] = list(range(200, 301, 10))
    pitches: List[int] = list(range(-4, 5, 1))

    for move_index in range(0, len(all_voice_moves)):
        move = all_voice_moves[move_index]
        for voice in voices:
            for rate in rates:
                for pitch in pitches:
                    engine.setProperty('voice', voice.id)
                    engine.setProperty('rate', rate)

                    file_name = os.path.basename(voice.id)
                    file_name += '-rate-' + str(rate)
                    file_name += '-pitch-' + str(pitch)
                    file_name += '.wav'
                    file_name = os.path.join(move_files_directory, all_text_moves[move_index], file_name)

                    if not os.path.isdir(os.path.join(move_files_directory, all_text_moves[move_index])):
                        os.mkdir(os.path.join(move_files_directory, all_text_moves[move_index]))

                    engine.save_to_file(move, file_name)

                    engine.runAndWait()

                    change_pitch(file_name, file_name, pitch)


def generate_polly_files():
    """
    Generates and saves audio files for all enumerated chess moves
    using the pyttsx3 engine. Parameters of the engine are varied to
    produce a large number files per move.

        ------------------- WARNING -------------------
    Amazon Polly operates on a pay-per system which can involve charges
    to your AWS account if you exceed usage amounts. Make sure you are
    within your usage limits before starting conversions.
    """

    session = boto3.Session(profile_name='adminuser')
    engine = boto3.client('polly', 'us-east-1')

    voices = ['Geraint']
    moves = ['hello world']

    try:

        for move_index in range(0, len(all_voice_moves)):
            move = all_voice_moves[move_index]
            for voice in voices:

                        file_name = os.path.basename(voice)
                        file_name += '.mp3'
                        file_name = os.path.join(move_files_directory, all_text_moves[move_index], file_name)

                        if not os.path.isdir(os.path.join(move_files_directory, all_text_moves[move_index])):
                            os.mkdir(os.path.join(move_files_directory, all_text_moves[move_index]))

                        response = engine.synthesize_speech(Text=move, OutputFormat="mp3",
                            VoiceId=voice)
                        
                        # Access the audio stream from the response
                        if "AudioStream" in response:
                            # Note: Closing the stream is important because the service throttles on the
                            # number of parallel connections. Here we are using contextlib.closing to
                            # ensure the close method of the stream object will be called automatically
                            # at the end of the with statement's scope.
                                with closing(response["AudioStream"]) as stream:
                                    output = file_name

                                try:
                                    # Open a file for writing the output as a binary stream
                                    with open(output, "wb") as file:
                                        file.write(stream.read())
                                except IOError as error:
                                    # Could not write to file, exit gracefully
                                    print(error)
                                    sys.exit(-1)

                        else:
                            # The response didn't contain audio data, exit gracefully
                            print("Could not stream audio")
                            sys.exit(-1)

    except (BotoCoreError, ClientError) as error:
        print(error)
        sys.exit(-1)


if __name__ == "__main__":

    if not os.path.isdir(move_files_directory):
        os.mkdir(move_files_directory)

    generate_pyttsx3_files()