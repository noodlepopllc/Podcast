from plan10.lib.qwen_llm import llm_analyze_media

import re

def scan_sentence(sentence: str) -> dict:
    """
    Full LTX2.3 risk scanner.
    Flags:
    - phoneme clusters (compression hazards)
    - low-energy endings (Whisper truncation)
    - multi-fricative endings
    - missing pauses
    - breath-unit overload
    - double-compression zones
    - sibilant/plosive density (secondary signal)
    """

    s = sentence.lower().strip()
    words = s.split()
    word_count = len(words)

    issues = []

    # -----------------------------
    # 1. Phoneme cluster detection
    # -----------------------------
    cluster_patterns = [
        r"spr", r"str", r"sk", r"st", r"pl", r"tr", r"nt", r"th"
    ]
    cluster_hits = sum(len(re.findall(p, s)) for p in cluster_patterns)

    if cluster_hits >= 2:
        issues.append("cluster_double_compression")
    elif cluster_hits == 1:
        issues.append("cluster_compression")

    # -----------------------------
    # 2. Low-energy ending detection
    # -----------------------------
    if re.search(r"(s|z|sh|th|f|r)\.$", s):
        issues.append("low_energy_ending")

    # -----------------------------
    # 3. Multi-fricative ending words
    # -----------------------------
    fricative_endings = ["sources", "research", "news", "percent", "million"]
    if any(s.endswith(w + ".") for w in fricative_endings):
        issues.append("multi_fricative_ending")

    # -----------------------------
    # 4. Missing pauses (single clause)
    # -----------------------------
    if not re.search(r",|;|—|-", sentence):
        issues.append("no_pause")

    # -----------------------------
    # 5. Breath-unit overload
    # -----------------------------
    if word_count > 14:
        issues.append("breath_unit_overload")

    # -----------------------------
    # 6. Sibilant / plosive density
    # -----------------------------
    sibilants = len(re.findall(r"[szx]|sh|ch", s))
    plosives = len(re.findall(r"[pbtdkg]", s))

    sib_density = sibilants / word_count if word_count else 0
    plo_density = plosives / word_count if word_count else 0

    if sib_density > 0.45:
        issues.append("high_sibilant_density")
    if plo_density > 0.80:
        issues.append("high_plosive_density")

    # -----------------------------
    # 7. Micro-stutter risk
    # -----------------------------
    if len(re.findall(r"(?:s|th|t|p)\s+(?:s|th|t|p)", s)) > 1:
        issues.append("micro_stutter_risk")

    return {
        "sentence": sentence,
        "word_count": word_count,
        "cluster_hits": cluster_hits,
        "sib_density": sib_density,
        "plo_density": plo_density,
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
                template = prompt.format(sentence=result['sentence'], issues=result['issues'], issues=args.persona)
                new_sentences = llm_analyze_media('',prompt=template)['analysis']
                for asentence in new_sentences.split('\n'):
                    new_complete = f'{who}: {asentence}'
                    print(new_complete)
                    outputs.append(new_complete)
            else:
                outputs.append(line.strip())
    with open(args.output, 'w') as to_write:
        for output in outputs:
            to_write.write(f'{output}\n')

if __name__ == '__main__':
    main()