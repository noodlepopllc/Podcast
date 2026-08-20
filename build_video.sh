#!/bin/bash
set -euo pipefail

mkdir -p current_podcast

if [[ ! -f current_podcast/gamingnews.txt ]]; then
    rm -f current_podcast/*
    rm -f podcast_wavs/*
    rm -f podcast_wavs_out/*
    uv run scripts/get_news.py -G -O current_podcast/gamingnews.txt
    uv run llm -S current_podcast/gamingnews.txt -M 32786 -P " " -O current_podcast/gamingnews_script.txt
    uv run scripts/to_script.py -I current_podcast/gamingnews_script.txt -S Gamer -O current_podcast/gamer_podcast.txt
    uv run scriptreader -s -i current_podcast/gamer_podcast.txt -o podcast_wavs
    uv run scripts/combiner.py podcast_wavs podcast_wavs_out
fi

mkdir -p current_newscast

if [[ ! -f current_newscast/worldnews.txt ]]; then
    rm -f current_newscast/*
    rm -f newscast_wavs/*
    rm -f newscast_wavs_out/*
    uv run scripts/get_news.py -O current_newscast/worldnews.txt
    uv run llm -S current_newscast/worldnews.txt -M 32786 -P " " -O current_newscast/worldnews_script.txt
    uv run scripts/to_script.py -I current_newscast/worldnews_script.txt -S Anchor -O current_newscast/anchor_newscast.txt
    uv run scriptreader -s -i current_newscast/anchor_newscast.txt -o newscast_wavs
    uv run scripts/combiner.py newscast_wavs newscast_wavs_out
fi

mkdir -p media

GAMER="media/gamer.png"
if [[ ! -f "$GAMER" ]]; then
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female gaming podcaster sitting in front of her computer, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, professional streamer setup with monitor glow." -O "$GAMER" -W 720 -H 1280
fi

GAMER_VOICE="media/gamer.wav"
if [[ ! -f "$GAMER_VOICE" ]]; then
    uv run dialog -I "young adult, female, high pitch, american accent" -O "$GAMER_VOICE" 
fi

ANCHOR="media/anchor.png"
if [[ ! -f "$ANCHOR" ]]; then
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female East Indian newscaster sitting at a spacious news desk, warm confident smile, engaged expression with slightly raised eyebrows, subtle forward‑leaning posture, long wavy black hair with realistic strands and natural highlights, business blazer, natural skin texture with subtle imperfections, mature feminine facial proportions, soft warm studio lighting with gentle highlights, wider professional news studio environment, open composition." -O "$ANCHOR" -W 720 -H 1280
fi

ANCHOR_VOICE="media/anchor.wav"
if [[ ! -f "$ANCHOR_VOICE" ]]; then
    uv run dialog -I "young adult, female, moderate pitch, british accent" -O "$ANCHOR_VOICE" 
fi

MODE=${1:-0}

INPUT_DIR="podcast_wavs_out"
OUTPUT_DIR="videos"
prefix="gamer"
ACTOR="$GAMER"
PROMPT="She speaks with excitement and enthusiasm as she sits behind the desk with a smile. "
REF="$GAMER_VOICE"

if [[ "$MODE" -eq 1 ]]; then
    INPUT_DIR="newscast_wavs_out"
    prefix="anchor"
    ACTOR="$ANCHOR"
    PROMPT="She speaks calmly with a neutral pleasing smile. "
    REF="$ANCHOR_VOICE"
fi

mkdir -p "$OUTPUT_DIR"

for wav in "$INPUT_DIR"/clip_*.wav; do
    [[ -e "$wav" ]] || continue

    base=$(basename "$wav" .wav)
    num=${base#clip_}
    out="$OUTPUT_DIR/${prefix}${num}.mp4"

    if [[ -f "$out" ]]; then
        echo "Skipping $wav — output already exists: $out"
        continue
    fi

    echo "Processing $wav -> $out"

    transcript="$OUTPUT_DIR/clip${num}.txt"

    uv run dialog -R "$wav" -S -O "$transcript"

    duration=$(cut -d'|' -f1 "$transcript")
    duration=$((duration + 1))
    text=$(cut -d'|' -f2 "$transcript")

    #wav="$OUTPUT_DIR/clip${num}.wav"
    
    #uv run dialog -R "$REF" -T "$text" -D $duration -O $wav

    uv run speech_to_video \
        -A "$REF" \
        -T "Start. $text Stop." \
        -P "$PROMPT" \
        -I "$ACTOR" \
        -D "$duration" \
        -O "$out"
done

