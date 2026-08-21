import sys, os, requests, librosa
from pathlib import Path
from json import dump, load
import soundfile as sf
import numpy as np
from spacy_download import load_spacy
from plan10.lib.dialog import CloneVoice, DialogSession

# uv run spacy download en_core_web_sm

class Voice(object):

    def __init__(self, config_path, segment, output):
        self.segment = segment
        self.config_path = config_path
        with open(config_path, 'r') as infile:
            self.config = load(infile)
        self.output = output


    def readScript(self, script):
        nlp = load_spacy("en_core_web_sm", exclude=["parser", "tagger"])
        nlp.add_pipe('sentencizer')

        # Step 1: read lines and sentence‑split
        raw_segments = []   # list of (key, text)

        with open(script, 'r') as infile:
            for line in infile:
                l = line.replace("*", "")
                key = l.split(':')[0].split(' ')[0].lower().strip()
                rest = l.split(':', 1)
                if len(rest) > 1:
                    text = rest[1].strip()
                else:
                    continue

                if not key:
                    continue

                if self.segment:
                    doc = nlp(text)
                    for s in doc.sents:
                        raw_segments.append((key, str(s).strip()))
                else:
                    raw_segments.append((key, text.strip()))

        # Step 2: merge segments into 10–22 word chunks
        merged = []
        current_key = None
        current_text = []

        MIN_WORDS = 10
        MAX_WORDS = 15

        for key, seg in raw_segments:
            words = seg.split()

            # If starting a new speaker block
            if current_key is None:
                current_key = key
                current_text = words
                continue

            # If same speaker, try merging
            if key == current_key:
                if len(current_text) + len(words) <= MAX_WORDS:
                    current_text.extend(words)
                else:
                    # finalize current
                    merged.append({current_key: " ".join(current_text)})
                    current_key = key
                    current_text = words
            else:
                # speaker changed → finalize current
                merged.append({current_key: " ".join(current_text)})
                current_key = key
                current_text = words

        # finalize last
        if current_key is not None:
            merged.append({current_key: " ".join(current_text)})

        return merged


    def existing(self, js):
        if os.path.exists(js):
            with open(js,'r') as f:
                return load(f)
        return []


    def create_wav(self, text, path='tmp2.wav', key='', session=None):
        voice = self.config[key]['voice']
        CloneVoice(text, voice, path, 15.0, lengthen=False, session=session)
        return round(librosa.get_duration(path=path),2)

    def run(self, script):
        jsonpath = script.split('.')[-2] + '.json'
        outp = self.existing(jsonpath)
        inp = self.readScript(script)
        if len(outp) == len(inp):
            return
        prefix = Path(script).stem

        Path(self.output).mkdir(parents=True, exist_ok=True)

        with DialogSession() as tts:
            for idx in range(len(outp),len(inp)):
                key = [x for x in inp[idx].keys()][0]
                if key not in self.config:
                    key = 'alex'
                text = inp[idx][key]
                voice = self.config[key]
                p = f'{self.output}/{prefix}_{idx:03}_{key}.wav'
                inp[idx]['path'] = p
                inp[idx]['duration'] = self.create_wav(text, p, key, tts)
                outp.append(inp[idx])
        with open(jsonpath,'w') as outfile:
            dump(outp,outfile,indent=4)

def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Create voices')
    parser.add_argument('-i','--input', type=str, default=None, help='script path')
    parser.add_argument('-s', '--segment', action='store_true', help='segment sentences')
    parser.add_argument('-c', '--config', type=str, default='data/config.json', help='config file')
    parser.add_argument('-r', '--reference', type=str, default='', help='cloned voice')
    parser.add_argument('-n', '--name', type=str, default='alex', help='name of person with cloned voice')
    parser.add_argument('-o', '--output', type=str, default='waves', help='directory to output wav files into')
    args = parser.parse_args()
    Path("data").mkdir(parents=True, exist_ok=True)
    voice = None
    config_path = args.config
    if not os.path.exists(config_path):
        with open(config_path, 'w') as outfile:
            dump({args.name.lower():{'voice':args.reference,'speed':1.0}}, outfile)
    voice = Voice(config_path, args.segment, output=args.output)
    if args.name:
        voice.config[args.name.lower()] = {'voice':args.reference,'speed':1.0}
    voice.run(args.input)
if __name__ == '__main__':
    main()

