#!/bin/bash
set -euo pipefail

uv run config -R
source .env

MODE=${1:-0}
mkdir -p media
OUTPUT_DIR="videos"

if [[ "$ANIME" != "False" ]]; then
    GEN_CMD="anime_gen"

    # Anime‑specific character descriptors
    DESC_NEWSCASTER="Young adult female newscaster seated at a spacious news desk, warm confident smile, slightly raised eyebrows, gentle forward‑leaning posture, long wavy hair with soft highlights, business blazer, friendly professional demeanor, holding a pen with papers on the desk, bright studio environment."
    DESC_GAMER="Young adult female gaming podcaster sitting in front of her computer, dark roots transitioning into blonde hair with soft pink tips, v‑neck green t‑shirt, energetic friendly expression, relaxed posture, streamer desk setup with glowing monitor."
    DESC_SCIENTIST="Young adult half‑Asian educator with a short blonde bobcut with dark roots, wearing reading glasses, fitted white camisole top, warm friendly expression, confident posture, standing in a bright modern library with sunlit windows."

else
    GEN_CMD="image_gen"

    # Realistic descriptors
    DESC_NEWSCASTER="Photorealistic portrait of a beautiful young adult female newscaster sitting at a spacious news desk, warm confident smile, engaged expression with slightly raised eyebrows, subtle forward‑leaning posture, long wavy black hair with realistic strands and natural highlights, business blazer, natural skin texture with subtle imperfections, mature feminine facial proportions, soft warm studio lighting with gentle highlights, wider professional news studio environment, open composition, holding a pen in one hand with papers on the desk."
    DESC_GAMER="Photorealistic portrait of a beautiful young adult female gaming podcaster sitting in front of her computer, dark natural roots transitioning into blonde hair with soft pink tips, realistic hair strands and natural highlights, v‑neck green t‑shirt, natural skin texture with subtle imperfections, mature feminine facial proportions, soft balanced studio lighting, professional streamer setup with monitor glow."
    DESC_SCIENTIST="Photorealistic medium closeup portrait of an attractive young adult half‑Asian influencer with a short blonde bobcut with dark roots, wearing thin low‑profile reading glasses with clear anti‑reflective lenses that do not obscure the eyes or cast shadows on the cheeks. Soft natural makeup, smooth natural skin, warm friendly expression, subtle confident posture, wearing a fitted white camisole top. Bright modern library with sunlit windows, soft frontal daylight that evenly illuminates the face and keeps the mouth, lips, and cheek curvature fully visible for accurate lipsync. Clean polished composition with unobstructed facial landmarks and no glare on the lenses."
fi



if [[ "$MODE" -eq 0 ]]; then
    ANCHOR="media/anchor.png"
    ANCHOR_VOICE="media/anchor.wav"
    prefix="newscast"
    if [[ ! -f "$ANCHOR" ]]; then
        uv run "$GEN_CMD" -P "$DESC_NEWSCASTER" -O "$ANCHOR" -W $WIDTH -H $HEIGHT
    fi


    if [[ ! -f "$ANCHOR_VOICE" ]]; then
        uv run dialog -I "young adult, female, moderate pitch, american accent" -O "$ANCHOR_VOICE" 
    fi

    if [[ ! -f current_newscast/worldnews.txt ]]; then
        rm -f current_newscast/*
        rm -f newscast_wavs/*
        #rm -f newscast_wavs_out/*
        mkdir -p current_newscast
        uv run scripts/get_news.py -R "feeds/news.txt" -P "prompts/news.txt" -O current_newscast/worldnews.txt -L 
        uv run llm -S current_newscast/worldnews.txt -M 32786 -P " " -O current_newscast/worldnews_script.txt
        uv run scripts/to_script.py -I current_newscast/worldnews_script.txt -S Anchor -O current_newscast/$prefix.txt
        uv run scripts/rewriter.py -I current_newscast/$prefix.txt -O "current_newscast/${prefix}_rewritten.txt" 
        #uv run scripts/combiner.py newscast_wavs newscast_wavs_out
    fi

    uv run scripts/script_reader.py -s -i "current_newscast/${prefix}_rewritten.txt"  -r $ANCHOR_VOICE -n Anchor -o newscast_wavs


    INPUT_DIR="newscast_wavs"
    ACTOR="$ANCHOR"
    PROMPT="She speaks calmly with a neutral pleasing smile. "
    REF="$ANCHOR_VOICE"
fi

if [[ "$MODE" -eq 1 ]]; then
    GAMER="media/gamer.png"
    GAMER_VOICE="media/gamer.wav"
    prefix="podcast"
    
    if [[ ! -f "$GAMER" ]]; then
        uv run "$GEN_CMD" -P "$DESC_GAMER" -O "$GAMER" -W $WIDTH -H $HEIGHT
    fi


    if [[ ! -f "$GAMER_VOICE" ]]; then
        uv run dialog -I "young adult, female, high pitch, american accent" -O "$GAMER_VOICE" 
    fi

    if [[ ! -f current_podcast/gamingnews.txt ]]; then
        rm -f current_podcast/*
        rm -f podcast_wavs/*
        #rm -f podcast_wavs_out/*
        mkdir -p current_podcast
        uv run scripts/get_news.py -R "feeds/gaming.txt" -P "prompts/gamer.txt" -O current_podcast/gamingnews.txt -L 
        uv run llm -S current_podcast/gamingnews.txt -M 32786 -P " " -O current_podcast/gamingnews_script.txt
        uv run scripts/to_script.py -I current_podcast/gamingnews_script.txt -S Gamer -O current_podcast/$prefix.txt
        
        #uv run scripts/combiner.py podcast_wavs podcast_wavs_out
    fi

    uv run scripts/script_reader.py -s -i current_podcast/$prefix.txt  -r $GAMER_VOICE -n Gamer -o podcast_wavs

    INPUT_DIR="podcast_wavs"
    ACTOR="$GAMER"
    PROMPT="She speaks with excitement and enthusiasm as she sits behind the desk with a smile. "
    REF="$GAMER_VOICE"
fi

if [[ "$MODE" -eq 2 ]]; then
    SCIENTIST="media/scientist.png"
    SCIENTIST_VOICE="media/scientist.wav"
    prefix="educast"

    if [[ ! -f "$SCIENTIST" ]]; then
        #uv run image_gen -P "Photorealistic medium closeup portrait of an attractive young adult half‑Asian influencer with a short blonde bobcut with dark roots, wearing black‑rimmed reading glasses, soft natural makeup, a fitted white camisole top, casual modern slacks, smooth natural skin, warm friendly expression, subtle confident posture, standing in a bright modern library with sunlit windows, soft flattering daylight, clean polished composition." -O "$SCIENTIST" -W $WIDTH -H $HEIGHT
        uv run "$GEN_CMD" -P "$DESC_SCIENTIST" -O "$SCIENTIST" -W $WIDTH -H $HEIGHT
    fi


    if [[ ! -f "$SCIENTIST_VOICE" ]]; then
        uv run dialog -I "young adult, female, moderate pitch, american accent" -O "$SCIENTIST_VOICE" 
    fi

    if [[ ! -f current_educast/sciencenews.txt ]]; then
        rm -f current_educast/*
        rm -f educast_wavs/*
        #rm -f educast_wavs_out/*
        mkdir -p current_educast
        uv run scripts/get_news.py -R "feeds/science.txt" -P "prompts/science.txt" -O current_educast/sciencenews.txt -L 
        uv run llm -S current_educast/sciencenews.txt -M 32786 -P " " -O current_educast/sciencenews_script.txt
        uv run scripts/to_script.py -I current_educast/sciencenews_script.txt -S Scientist -O current_educast/$prefix.txt
        #uv run scripts/combiner.py educast_wavs educast_wavs_out
    fi

    uv run scripts/script_reader.py -s -i current_educast/$prefix.txt -r $SCIENTIST_VOICE -n Scientist -o educast_wavs

    INPUT_DIR="educast_wavs"
    ACTOR="$SCIENTIST"
    PROMPT="She speaks with enthusiasm and a subtle smile. "
    REF="$SCIENTIST_VOICE"
fi


mkdir -p "$OUTPUT_DIR"

for wav in "$INPUT_DIR"/${prefix}*.wav; do
    [[ -e "$wav" ]] || continue

    base=$(basename "$wav" .wav)
    num=${base#clip_}
    out="$OUTPUT_DIR/${prefix}_${num}.mp4"

    if [[ -f "$out" ]]; then
        echo "Skipping $wav — output already exists: $out"
        continue
    fi

    echo "Processing $wav -> $out"

    transcript="${wav%.*}.txt"

    echo "New transcript -> $transcript"

    duration=$(cut -d'|' -f1 "$transcript")
    duration=$((duration + 1))
    text=$(cut -d'|' -f2 "$transcript")

    uv run speech_to_video \
        -A "$REF" \
        -T "$text Plastic Waiter." \
        -P "$PROMPT" \
        -I "$ACTOR" \
        -D "$duration" \
        -O "$out"
done

echo "=================================================="
echo " FILE ISOLATION PASS"
echo "=================================================="

# 1. Grab today's system date in DDMMYY format
DATE_STR=$(date +"%d%m%y")
ARCHIVE_FOLDER="${DATE_STR}_${prefix}"

echo "Creating pristine run directory: $ARCHIVE_FOLDER"
mkdir -p "$ARCHIVE_FOLDER"

# 2. MOVE the fresh video files into the folder immediately 
# This completely clears out the raw output bucket so no strays can interfere
if ls "$OUTPUT_DIR"/${prefix}_*.mp4 1>/dev/null 2>&1; then
    mv "$OUTPUT_DIR"/${prefix}_*.mp4 "$ARCHIVE_FOLDER/"
    echo "Successfully moved all fresh raw files into $ARCHIVE_FOLDER/"
else
    echo "Warning: No matching generated files found to isolate."
fi

echo "=================================================="
echo " RUNNING COMPILER PIPELINE"
echo "=================================================="

echo "All generation and processing tasks successfully completed!"
