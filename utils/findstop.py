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


from pathlib import Path
import json

def get_stop_time_debug(json_file):
    timings = json.loads(Path(json_file).read_text())

    # Flatten all words across all segments
    all_words = []
    for si, seg in enumerate(timings['segments']):
        for w in seg['words']:
            all_words.append({
                "seg_index": si,
                "word": w['word'],
                "start": w['start'],
                "end": w['end'],
            })

    print("ALL WORDS:")
    for i, w in enumerate(all_words):
        print(f"{i}: [seg {w['seg_index']}] {w['word']} {w['start']} → {w['end']}")

    prev_end = None

    # Search backwards for "propeller"
    # Search backwards for "banana" safely
    for i in range(len(all_words)-1, -1, -1):
        w = all_words[i]
        # Using startswith handles "banana", "banana.", or "banana," seamlessly
        if w['word'].strip().lower().startswith("plastic"):
            print(f"\nFOUND PLASTIC BUFFER TRIGGER at index {i}: {w}")
            if i > 0:
                prev_end = all_words[i-1]['end']
                print(f"PREV TRUE WORD at index {i-1}: {all_words[i-1]}")
            else:
                print("NO PREV WORD (plastic is first)")
            
            stop_time = w['start']
            print(f"\nRETURNING stop_time={stop_time}, prev_end={prev_end}, isStop=True")
            return (stop_time, prev_end, True)

    # fallback
    last_word = all_words[-1]
    print(f"\nNO PROPELLER FOUND, FALLBACK TO LAST WORD: {last_word}")
    stop_time = last_word['end']
    print(f"RETURNING stop_time={stop_time}, prev_end=None, isStop=False")
    return (stop_time, None, False)

def stop_frame_from_sample(stop_sample, fps=24, sr=48000):
    stop_time = stop_sample / sr
    return round(stop_time * fps)


def sample_end(stop_time, sr=48000, fps=24, start=True):
    if start:
        return int(stop_time * sr) - ((sr // fps) * 3)
    else:
        return int(stop_time * sr) + ((sr // fps) * 8)

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

    # ----------------------------------------
    # 1. GET STOP TIME + PREV END (original timeline)
    # ----------------------------------------
    stop_time, prev_end, isStop = get_stop_time_debug(json_file)

    # ----------------------------------------
    # 2. SEMANTIC CUTOFF (original timeline)
    # ----------------------------------------
    if isStop and prev_end is not None:
        semantic_cut = int(0.5 * (prev_end + stop_time) * sr)
    else:
        semantic_cut = sample_end(stop_time, start=isStop)

    semantic_cut = min(semantic_cut, len(audio))

    # ----------------------------------------
    # 3. BACKWARD VOICED-REGION DETECTION (original timeline)
    # ----------------------------------------
    back_win = int(0.01 * sr)   # 10ms window
    voiced_thresh = 0.02        # voiced energy threshold

    refined_cut = semantic_cut

    for i in range(semantic_cut, back_win, -back_win):
        window = audio[i-back_win:i]
        energy = np.max(np.abs(window))

        if energy > voiced_thresh:
            refined_cut = i
            break

    # ----------------------------------------
    # 4. HARD TRIM END FIRST (correct order)
    # ----------------------------------------
    audio = audio[:refined_cut]

    # 50ms safety zeroing
    if len(audio) > 2400:
        audio[-2400:] = 0.0

    # ----------------------------------------
    # 5. VIDEO TRIM END FIRST (correct order)
    # ----------------------------------------
    stop_frame = stop_frame_from_sample(refined_cut)
    trim_video_frames_back(output, stop_frame)

    # ----------------------------------------
    # 6. NOW detect first sound (safe AFTER end trim)
    # ----------------------------------------
    start_sample = find_first_sound(audio)
    start_frame  = stop_frame_from_sample(start_sample)

    # ----------------------------------------
    # 7. TRIM FRONT LAST (correct order)
    # ----------------------------------------
    audio = audio[start_sample:]
    trim_video_frames_front(output, start_frame)

    # ----------------------------------------
    # 8. WRITE CLEAN AUDIO
    # ----------------------------------------
    sf.write(wav_file.replace('.wav', '_clean.wav'), audio, sr)


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
