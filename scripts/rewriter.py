from plan10.lib.qwen_llm import llm_analyze_media

import re

def scan_sentence(sentence: str) -> dict:
    s = sentence.lower().strip()
    words = s.split()
    word_count = len(words)
    issues = []

    # 1. Phoneme cluster detection (Look for 3+ clusters in the SAME sentence, or heavy multi-consonants)
    # Changed to count true high-risk clusters, ignoring simple "nt" or "th" unless frequent
    cluster_patterns = [r"spr", r"str", r"sk", r"st", r"pl", r"tr"]
    cluster_hits = sum(len(re.findall(p, s)) for p in cluster_patterns)
    
    # Only flag if there's a heavy concentration of friction
    if cluster_hits >= 3:
        issues.append("cluster_dense_friction")

    # 2. Low-energy ending detection
    if re.search(r"(sh|th|f)\.$", s): # Removed 's, z, r' as Kokoro handles trailing sibilants/rhotics fine
        issues.append("low_energy_ending")

    # 3. Multi-fricative ending words (Keep, these cause Whisper truncation)
    fricative_endings = ["sources", "research", "percent"]
    if any(s.endswith(w + ".") for w in fricative_endings):
        issues.append("multi_fricative_ending")

    # 4. Missing pauses (Only flag if sentence is long AND missing a pause)
    if word_count > 15 and not re.search(r",|;|—|-", sentence):
        issues.append("no_pause_in_long_span")

    # 5. Breath-unit overload (Adjusted to your true 18-22 word pipeline sweet spot)
    if word_count > 22:
        issues.append("breath_unit_overload")

    # 6. Micro-stutter risk (Look for colliding plosives across word boundaries)
    # Example: "stop playing" (p -> p) or "bad dog" (d -> d)
    if len(re.findall(r"(?:s|th|t|p)\s+(?:s|th|t|p)", s)) > 2: # Bumped threshold to 2+ instances
        issues.append("micro_stutter_risk")

    return {
        "sentence": sentence,
        "word_count": word_count,
        "issues": issues,
        "needs_rewrite": len(issues) > 0
    }



def scan_script(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [scan_sentence(s) for s in sentences if s.strip()]

def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--input', type=str, help="Path to script")
    parser.add_argument('-O', '--output', type=str, help="Output file")
    parser.add_argument('-P', '--persona', type=str, default='A news anchor for a night time television segment', help='persona of speaker')
    args = parser.parse_args()
    outputs = []
    prompt_path = 'prompts/sentence_enhance_agnostic.txt'
    prompt = Path(prompt_path).read_text()
    for line in Path(args.input).read_text().split('\n'):
        segments = line.split(':')
        who = segments[0]
        sentence = ': '.join(segments[1:])
        results = scan_script(sentence)
        for result in results:
            if result['needs_rewrite']:
                template = prompt.format(sentence=result['sentence'], issues=result['issues'], persona=args.persona)
                new_sentences = llm_analyze_media('',prompt=template)['analysis']
                for asentence in new_sentences.split('\n'):
                    new_complete = f'{who}: {asentence}'
                    print(asentence)
                    print(new_complete)
                    outputs.append(new_complete)
            else:
                outputs.append(line.strip())
    with open(args.output, 'w') as to_write:
        for output in outputs:
            to_write.write(f'{output}\n')

if __name__ == '__main__':
    main()