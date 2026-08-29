import json
from pathlib import Path
import numpy as np
import soundfile as sf
import math

import os
import shutil
from pathlib import Path

from PIL import Image
import numpy as np

def find_first_sound(audio, threshold=0.01):
    # absolute amplitude
    abs_audio = np.abs(audio)

    # find first index above threshold
    idx = np.argmax(abs_audio > threshold)

    # if no sound found, return 0
    return idx if abs_audio[idx] > threshold else 0

def trim_video_frames_front(frames_dir, start_frame):
    frames_dir = Path(frames_dir)
    frames = sorted(frames_dir.glob("*.png"))

    for f in frames:
        idx = int(f.stem)
        if idx < start_frame:
            f.unlink()

def trim_video_frames_back(frames_dir, stop_frame):
    frames_dir = Path(frames_dir)
    frames = sorted(frames_dir.glob("*.png"))

    for f in frames:
        idx = int(f.stem)
        if idx > stop_frame:
            f.unlink()


def get_stop_time(json_file):
    timings = json.loads(Path(json_file).read_text())
    words = timings['segments'][-1]['words']

    # Search backwards for the first word starting with "pop"
    for w in reversed(words):
        if w['word'].lower().startswith("propeller"):
            return w['start'], True

    # Fallback: use the last word's end time
    last_word = words[-1]
    return last_word['end'], False


def stop_frame_from_sample(stop_sample, fps=24, sr=48000):
    stop_time = stop_sample / sr
    return int(stop_time * fps)

def sample_end(stop_time, sr=48000, fps=24, start=True):
    if start:
        return int(stop_time * sr) - ((sr // fps) * 8)
    else:
        return int(stop_time * sr) + ((sr // fps) * 3)

def trim_video_frames(frames_dir, stop_frame):
    frames_dir = Path(frames_dir)
    frames = sorted(frames_dir.glob("*.png"))

    for f in frames:
        idx = int(f.stem)
        if idx > stop_frame:
            f.unlink()

    print("Trimmed to", stop_frame, "frames")

def trim_wav(json_file, wav_file, output):
    audio, sr = sf.read(wav_file)

    # FRONT TRIM (audio energy)
    start_sample = find_first_sound(audio)
    audio = audio[start_sample:]

    # BACK TRIM (WhisperX)
    stop_time, isStop = get_stop_time(json_file)
    stop_sample = sample_end(stop_time, start=isStop)
    audio = audio[:stop_sample]

    # --- TRAILING SILENCE DETECTION ---
    win = int(0.02 * sr)            # 20ms window
    threshold = 0.003               # RMS threshold
    required_silence = int(0.20*sr) # 200ms sustained silence

    silence_accum = 0
    cut_sample = len(audio)

    for i in range(stop_sample, len(audio), win):
        window = audio[i:i+win]
        if len(window) == 0:
            break

        rms = np.sqrt(np.mean(window**2))

        if rms < threshold:
            silence_accum += win
            if silence_accum >= required_silence:
                cut_sample = i
                break
        else:
            silence_accum = 0

    # Zero out trailing audio
    audio[cut_sample:] = 0.0

    # write cleaned audio
    sf.write(wav_file.replace('.wav', '_clean.wav'), audio, sr)

    # VIDEO TRIM
    start_frame = stop_frame_from_sample(start_sample)
    stop_frame  = stop_frame_from_sample(stop_sample)

    trim_video_frames_front(output, start_frame)
    trim_video_frames_back(output, stop_frame)



def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--input', type=str, help='Input file')
    parser.add_argument('-O', '--output', type=str, help='Output dir')
    args = parser.parse_args()
    tmp = ''.join(args.input.split('.')[:-1])
    input_files = []
    for x in ['.json','.wav']:
        tmpfile = tmp+x
        if Path(tmpfile).exists():
            input_files.append(tmpfile)
    input_files.append(args.output)

    trim_wav(*input_files)

if __name__ == '__main__':
    main()
