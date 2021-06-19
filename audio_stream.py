from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import pathlib

THRESHOLD = 1000
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000


def is_silent(waveform):
    return max(waveform) < THRESHOLD

def normalize(waveform):
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in waveform)

    r = array('h')
    for i in waveform:
        r.append(int(i*times))
    return r

def save_to_file(path, sample_width, data):
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()
    
def record(callback, endless=False):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, 
        channels=1, 
        rate=RATE,
        input=True, 
        output=True,
        frames_per_buffer=CHUNK_SIZE
    )

    silence_len = 0
    sound_started = False
    sound_stopped = False
    
    num_records = 1

    r = array('h')
    sample_width = p.get_sample_size(FORMAT)

    while True:
        waveform = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            waveform.byteswap()
        r.extend(waveform)

        silent = is_silent(waveform)
        
        if silent and sound_started:
            if not sound_stopped and silence_len > 0:
                sound_stopped = True
                sound_started = False
                
                if len(r) >= 16000: 
                    print('Sound is too long!')                
                elif len(r) > 5000:
                    file_name = './data/record_data/test/'  + str(num_records) + '.wav'
                    file = save_to_file(file_name, sample_width, normalize(r))
                    callback(file_name)                        
                else: 
                    print('Sound is too short!')
                    
                r = array('h')
                silence_len = 0
                
            silence_len += 1
        elif not silent and not sound_started:
            sound_started = True
            sound_stopped = False
            silence_len = 0
            if len(r) >= 2000:
                r = r[len(r) - 2000:]            
            print('Sound detected!')
        elif silent: 
            silence_len +=1
            
        if not endless and silence_len > 50:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
