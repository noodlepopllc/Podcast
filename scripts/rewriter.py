from plan10.lib.qwen_llm import llm_analyze_media

import re

def scan_sentence(sentence: str) -> dict:
    s = sentence.lower().strip()
    words = s.split()
    word_count = len(words)
    issues = []

    if word_count == 0:
        return {"sentence": sentence, "word_count": 0, "issues": [], "needs_rewrite": False}

    # === FIXED: Text-Based Phonetic Sibilance Tracker ===
    # 1. Standard literal sibilants
    sibilant_count = len(re.findall(r'[sz]', s))
    
    # 2. Hard-to-catch soft 'c' sounds (ce, ci, cy) like "sentence", "fences", "decide"
    soft_c_count = len(re.findall(r'c[eiy]', s))
    
    # 3. Fricative combos (sh, ch, x as 'ks')
    fricative_combos = len(re.findall(r'(sh|ch|x)', s))
    
    total_sibilance = sibilant_count + soft_c_count + fricative_combos
    sibilance_ratio = total_sibilance / word_count

    # Flag if sentence has high sibilant sound concentration
    if sibilance_ratio > 0.35 or total_sibilance >= 5:
        issues.append("heavy_sibilance_friction")

    # === Rest of your existing checks ===
    # 1. Phoneme cluster detection 
    cluster_patterns = [r"spr", r"str", r"sk", r"st", r"pl", r"tr"]
    cluster_hits = sum(len(re.findall(p, s)) for p in cluster_patterns)
    if cluster_hits >= 3:
        issues.append("cluster_dense_friction")

    # 2. Low-energy ending detection (Added soft 'ce' to endings to prevent truncation)
    if re.search(r"(sh|th|f|ce)\.$", s): 
        issues.append("low_energy_ending")

    # 3. Multi-fricative ending words 
    fricative_endings = ["sources", "research", "percent"]
    if any(s.endswith(w + ".") for w in fricative_endings):
        issues.append("multi_fricative_ending")

    # 4. Missing pauses 
    if word_count > 15 and not re.search(r",|;|—|-", sentence):
        issues.append("no_pause_in_long_span")

    # 5. Breath-unit overload 
    if word_count > 22:
        issues.append("breath_unit_overload")

    # 6. Micro-stutter risk 
    if len(re.findall(r"(?:s|th|t|p)\s+(?:s|th|t|p)", s)) > 2: 
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
                print(result['issues'])
                new_sentences = llm_analyze_media('',prompt=template)['analysis']
                for asentence in new_sentences.split('\n'):
                    new_complete = f'{who}: {asentence}'
                    print(sentence)
                    print(new_complete)
                    outputs.append(new_complete)
            else:
                outputs.append(line.strip())
    with open(args.output, 'w') as to_write:
        for output in outputs:
            to_write.write(f'{output}\n')

if __name__ == '__main__':
    main()