#!/bin/bash
set -euo pipefail

MODE=${1:-0}
mkdir -p media
OUTPUT_DIR="videos"

if [[ "$MODE" -eq 0 ]]; then
    ANCHOR="media/anchor.png"
    ANCHOR_VOICE="media/anchor.wav"

    if [[ ! -f current_newscast/worldnews.txt ]]; then
        rm -f current_newscast/*
        rm -f newscast_wavs/*
        rm -f newscast_wavs_out/*
        mkdir -p current_newscast
        uv run scripts/get_news.py -O current_newscast/worldnews.txt
        uv run llm -S current_newscast/worldnews.txt -M 32786 -P " " -O current_newscast/worldnews_script.txt
        uv run scripts/to_script.py -I current_newscast/worldnews_script.txt -S Anchor -O current_newscast/anchor_newscast.txt
        uv run scriptreader -s -i current_newscast/anchor_newscast.txt -o newscast_wavs
        uv run scripts/combiner.py newscast_wavs newscast_wavs_out
    fi

    if [[ ! -f "$ANCHOR" ]]; then
        uv run image_gen -P "Photorealistic portrait of a beautiful young adult female newscaster sitting at a spacious news desk, warm confident smile, engaged expression with slightly raised eyebrows, subtle forward‑leaning posture, long wavy black hair with realistic strands and natural highlights, business blazer, natural skin texture with subtle imperfections, mature feminine facial proportions, soft warm studio lighting with gentle highlights, wider professional news studio environment, open composition, holding a pen in one hand with papers on the desk." -O "$ANCHOR" -W 720 -H 1280
    fi


    if [[ ! -f "$ANCHOR_VOICE" ]]; then
        uv run dialog -I "young adult, female, moderate pitch" -O "$ANCHOR_VOICE" 
    fi

    INPUT_DIR="newscast_wavs_out"
    prefix="anchor"
    ACTOR="$ANCHOR"
    PROMPT="She speaks calmly with a neutral pleasing smile. "
    REF="$ANCHOR_VOICE"
fi

if [[ "$MODE" -eq 1 ]]; then
    GAMER="media/gamer.png"
    GAMER_VOICE="media/gamer.wav"
    if [[ ! -f current_podcast/gamingnews.txt ]]; then
        rm -f current_podcast/*
        rm -f podcast_wavs/*
        rm -f podcast_wavs_out/*
        mkdir -p current_podcast
        uv run scripts/get_news.py -G -O current_podcast/gamingnews.txt
        uv run llm -S current_podcast/gamingnews.txt -M 32786 -P " " -O current_podcast/gamingnews_script.txt
        uv run scripts/to_script.py -I current_podcast/gamingnews_script.txt -S Gamer -O current_podcast/gamer_podcast.txt
        uv run scriptreader -s -i current_podcast/gamer_podcast.txt -o podcast_wavs
        uv run scripts/combiner.py podcast_wavs podcast_wavs_out
    fi

    if [[ ! -f "$GAMER" ]]; then
        uv run image_gen -P "Photorealistic portrait of a beautiful young adult female gaming podcaster sitting in front of her computer, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, professional streamer setup with monitor glow." -O "$GAMER" -W 720 -H 1280
    fi


    if [[ ! -f "$GAMER_VOICE" ]]; then
        uv run dialog -I "young adult, female, high pitch" -O "$GAMER_VOICE" 
    fi

    INPUT_DIR="podcast_wavs_out"
    prefix="gamer"
    ACTOR="$GAMER"
    PROMPT="She speaks with excitement and enthusiasm as she sits behind the desk with a smile. "
    REF="$GAMER_VOICE"
fi

if [[ "$MODE" -eq 2 ]]; then
    SCIENTIST="media/scientist.png"
    SCIENTIST_VOICE="media/scientist.wav"

    if [[ ! -f current_educast/sciencenews.txt ]]; then
        rm -f current_educast/*
        rm -f educast_wavs/*
        rm -f educast_wavs_out/*
        mkdir -p current_educast
        uv run scripts/get_news.py -S -O current_educast/sciencenews.txt
        uv run llm -S current_educast/sciencenews.txt -M 32786 -P " " -O current_educast/sciencenews_script.txt
        uv run scripts/to_script.py -I current_educast/sciencenews_script.txt -S Scientist -O current_educast/science_educast.txt
        uv run scriptreader -s -i current_educast/science_educast.txt -o educast_wavs
        uv run scripts/combiner.py educast_wavs educast_wavs_out
    fi

    if [[ ! -f "$SCIENTIST" ]]; then
        uv run image_gen -P "Photorealistic portrait of an attractive young adult half‑Asian influencer with a short blonde bobcut with dark roots, wearing black‑rimmed reading glasses, soft natural makeup, a fitted white camisole top, casual modern slacks, smooth natural skin, warm friendly expression, subtle confident posture, standing in a bright modern library with sunlit windows, soft flattering daylight, clean polished composition." -O "$SCIENTIST" -W 720 -H 1280
    fi


    if [[ ! -f "$SCIENTIST_VOICE" ]]; then
        uv run dialog -I "young adult, female, moderate pitch" -O "$SCIENTIST_VOICE" 
    fi

    INPUT_DIR="educast_wavs_out"
    prefix="scientist"
    ACTOR="$SCIENTIST"
    PROMPT="She speaks with enthusiasm and a subtle smile. "
    REF="$SCIENTIST_VOICE"
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

    transcript="$OUTPUT_DIR/${prefix}${num}.txt"

    uv run dialog -R "$wav" -S -O "$transcript"

    duration=$(cut -d'|' -f1 "$transcript")
    duration=$((duration + 1))
    text=$(cut -d'|' -f2 "$transcript")

    #wav="$OUTPUT_DIR/clip${num}.wav"
    
    #uv run dialog -R "$REF" -T "$text" -D $duration -O $wav

    uv run speech_to_video \
        -A "$REF" \
        -T "$text Stop." \
        -P "$PROMPT" \
        -I "$ACTOR" \
        -D "$duration" \
        -O "$out"
done

