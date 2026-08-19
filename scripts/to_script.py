import re
from pathlib import Path

def extract_spoken_lines(text: str):
    # Remove everything after Read More
    text = re.split(r"\*\*Read More\*\*", text)[0]

    paragraphs = re.split(r"\n\s*\n", text)
    lines = []

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        # Remove markdown bold/italic
        p = p.replace("**", "")
        p = p.replace("*", "")

        # Remove URLs
        p = re.sub(r"https?://\S+", "", p)

        # Skip numbered URL list items only
        if re.match(r"^\d+\.\s+https?://", p):
            continue

        # Remove leftover bullets
        p = re.sub(r"^[\*\-]+\s*", "", p)

        # Normalize spacing
        p = re.sub(r"\s{2,}", " ", p).strip()

        if not p:
            continue

        # 🔥 Split on sentence endings OR newline boundaries
        raw_lines = re.split(r"(?<=[.!?])\s+|\n+", p)

        for line in raw_lines:
            line = line.strip()
            if line:
                lines.append(line)

    return lines


def to_scriptreader_format(lines, speaker="Anchor"):
    return "\n".join(f"{speaker}: {line}" for line in lines)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--input', default=None, help='input script')
    parser.add_argument('-S', '--speaker', default='Anchor', help='person speaking')
    parser.add_argument('-O', '--output', default='script.txt', help='name of script file')
    args = parser.parse_args()
    # Load your generated news briefing
    briefing_text = Path(args.input).read_text()

    # Extract spoken narration
    spoken_lines = extract_spoken_lines(briefing_text)

    # Convert to ScriptReader format
    scriptreader_text = to_scriptreader_format(spoken_lines, speaker=args.speaker)

    # Save output
    Path(args.output).write_text(scriptreader_text)

    print(f"Created {args.output} — ready for ScriptReader WAV generation.")


if __name__ == "__main__":
    main()

