#!/bin/bash
set -euo pipefail

mkdir -p current
#uv run scripts/get_news.py -G -O current/gamingnews.txt
#uv run scripts/get_news.py -O current/worldnews.txt
#uv run llm -S current/gamingnews.txt -M 32786 -P " " -O current/gamingnews_script.txt
#uv run llm -S current/worldnews.txt -M 32786 -P " " -O current/worldnews_script.txt
#uv run scripts/to_script.py -I current/gamingnews_script.txt -S Gamer -O current/gamer_podcast.txt
#uv run scripts/to_script.py -I current/worldnews_script.txt -S Gamer -O current/anchor_newscast.txt
#uv run scriptreader -s -i current/gamer_podcast.txt -o podcast_wavs
#uv run scriptreader -s -i current/anchor_newscast.txt -o newscast_wavs
#uv run scripts/combiner.py podcast_wavs podcast_wavs_out
#uv run scripts/combiner.py newscast_wavs newscast_wavs_out

mkdir -p media



INPUT_DIR="podcast_wavs_out"
OUTPUT_DIR="podcast_videos"
GAMER="media/gamer.png"
GAMER_2="media/gamer2.png"
GAMER_3="media/gamer3.png"
GAMER_4="media/gamer4.png"
if [[ ! -f $GAMER ]]; then
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female gaming podcaster sitting in front of her computer, natural skin texture with visible pores, mature feminine facial proportions, subtle imperfections, realistic facial details, soft balanced studio lighting, detailed hair strands, non‑glossy skin, professional streamer setup, high‑resolution realism." -O "$GAMER_2" -W 720 -H 1280 
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female gaming podcaster sitting in front of her computer, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, professional streamer setup with monitor glow." -O $GAMER -W 720 -H 1280
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female gaming podcaster, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, sitting in front of a clean neutral studio background with no visible screens, monitors, or glowing electronics." -O $GAMER_3 -W 720 -H 1280 
    uv run image_gen -P "Photorealistic portrait of a beautiful adult female gaming podcaster, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, sitting at her desk with a professional podcast microphone on a boom arm, subtle acoustic panels and a softly blurred studio background, no visible screens or monitors." -O $GAMER_4 -W 720 -H 1280 
fi
GAMER_VOICE="media/gamer.wav"
if [[ ! -f $GAMER_VOICE ]];then
    uv run dialog -I "young adult, female, high pitch, american accent" -O $GAMER_VOICE -L
fi
ACTOR=$GAMER
PROMPT="She speaks with excitement and enthusiasm as she sits behind the desk with a smile. "
REF=$GAMER_VOICE
mkdir -p "$OUTPUT_DIR"

for wav in "$INPUT_DIR"/clip_*.wav; do
    # Ensure the glob actually matched files
    [[ -e "$wav" ]] || continue

    base=$(basename "$wav" .wav)      # clip_001
    num=${base#clip_}                 # 001
    out="$OUTPUT_DIR/clip${num}.mp4"  # video/clip001.mp4

    if [[ -f "$out" ]]; then
        echo "Skipping $wav — output already exists: $out"
        continue
    fi

    echo "Processing $wav -> $out"
    transcript="$OUTPUT_DIR/clip${num}.txt"
    
    uv run dialog -R "$wav" -S -O "$transcript"
    
    # Corrected command substitutions
    duration=$(cut -d'|' -f1 "$transcript")
    duration=$((duration + 1))
    text=$(cut -d'|' -f2 "$transcript")
    
    #wav="$OUTPUT_DIR/clip${num}.wav"
    
    #uv run dialog -R "$REF" -T "$text" -D $duration -O $wav
    
    # Corrected line continuations and missing backslashes
    uv run speech_to_video \
        -A "$REF" \
        -T "$text" \
        -P "$PROMPT" \
        -I "$ACTOR" \
        -D "$duration" \
        -O "$out"
done

