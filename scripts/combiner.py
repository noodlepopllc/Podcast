import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

PREF_MIN = 8.0
PREF_MAX = 10.0
HARD_MIN = 4.0
HARD_MAX = 15.0

TOP_DB = 32
MIN_SILENCE = 0.22   # minimum silence length in seconds


def load_audio(path):
    y, sr = librosa.load(path, sr=None)
    return y, sr


def pad_to_full_second(audio, sr):
    dur = librosa.get_duration(y=audio, sr=sr)
    target = np.ceil(dur)
    pad_samples = int((target - dur) * sr)
    if pad_samples > 0:
        audio = np.concatenate([audio, np.zeros(pad_samples, dtype=audio.dtype)])
    return audio


def concatenate_all_wavs(wavs):
    audios = []
    sr = None

    for w in wavs:
        y, sr = load_audio(w)
        sil = np.zeros(int(sr * 0.50))  # 500ms silence at end only

        audios.append(y)
        audios.append(sil)

    return np.concatenate(audios), sr


def get_silence_segments(y, sr):
    intervals = librosa.effects.split(y, top_db=TOP_DB)

    silences = []
    last_end = 0

    for start, end in intervals:
        if start > last_end:
            silences.append((last_end, start))
        last_end = end

    if last_end < len(y):
        silences.append((last_end, len(y)))

    filtered = []
    for s, e in silences:
        dur = (e - s) / sr
        if dur >= MIN_SILENCE:
            filtered.append((s, e))

    return filtered, intervals


def segment_by_silence(y, sr, silences):
    clips = []
    current_audio = []
    current_len = 0.0

    cut_points = [s for s, e in silences]
    last_cut = 0

    for cut in cut_points:
        chunk = y[last_cut:cut]
        chunk_dur = librosa.get_duration(y=chunk, sr=sr)

        # accumulate until PREF_MAX
        if current_len + chunk_dur <= PREF_MAX:
            current_audio.append(chunk)
            current_len += chunk_dur
        else:
            # if too short, force-include
            if current_len < PREF_MIN:
                current_audio.append(chunk)
                current_len += chunk_dur
            else:
                clips.append(np.concatenate(current_audio))
                current_audio = [chunk]
                current_len = chunk_dur

        # HARD_MAX enforcement
        if current_len >= HARD_MAX:
            clips.append(np.concatenate(current_audio))
            current_audio = []
            current_len = 0.0

        last_cut = cut

    # final chunk
    if last_cut < len(y):
        chunk = y[last_cut:]
        current_audio.append(chunk)

    if current_audio:
        clips.append(np.concatenate(current_audio))

    return clips


def enforce_minimums(clips, sr):
    final = []
    buffer = []

    for clip in clips:
        dur = librosa.get_duration(y=clip, sr=sr)

        if dur < HARD_MIN:
            buffer.append(clip)
            continue

        if buffer:
            merged = np.concatenate(buffer)
            merged_dur = librosa.get_duration(y=merged, sr=sr)

            if merged_dur < HARD_MIN:
                merged = np.concatenate([merged, clip])
                final.append(merged)
            else:
                final.append(merged)
                final.append(clip)

            buffer = []
        else:
            final.append(clip)

    if buffer:
        final.append(np.concatenate(buffer))

    return final


def save_clips(clips, sr, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    report_lines = []
    idx = 1

    for clip in clips:
        clip = pad_to_full_second(clip, sr)
        dur = librosa.get_duration(y=clip, sr=sr)

        out_path = out_dir / f"clip_{idx:03d}.wav"
        sf.write(out_path, clip, sr)

        report_lines.append(f"{out_path.name} | {dur:.2f}s")
        idx += 1

    (out_dir / "clip_report.txt").write_text("\n".join(report_lines))


def process_all(in_dir, out_dir):
    in_dir = Path(in_dir)
    wavs = sorted(in_dir.glob("*.wav"))

    y_all, sr = concatenate_all_wavs(wavs)
    silences, intervals = get_silence_segments(y_all, sr)
    clips = segment_by_silence(y_all, sr, silences)
    clips = enforce_minimums(clips, sr)
    save_clips(clips, sr, out_dir)


if __name__ == "__main__":
    import sys
    process_all(sys.argv[1], sys.argv[2])
