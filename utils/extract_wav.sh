INPUT_DIR=$1
WORK=$2

mkdir -p $WORK
mkdir -p "$WORK/A"
mkdir -p "$WORK/B"

INBOUND="$WORK/A"
WORKING="$WORK/B"
TMP=$INBOUND

files=($(ls $INPUT_DIR/*.mp4 2>/dev/null))
num_files=${#files[@]}
y=0
for ((i=0; i<num_files; i++)); do
    INPUT="${files[$i]}"
    echo $INPUT

    basename="${INPUT##*/}"
    echo "$basename"
    output="$WORK/${basename%.mp4}.wav"

    ffmpeg -i "$INPUT" -vn -ac 1 -ar 48000 "$output"
    ffmpeg -i "$INPUT" -an -r 24 -vf "fps=24" "$INBOUND/%06d.png"

    uvx --from openai-whisper whisper $output --language English --task transcribe --output_format json --model large-v2 --clip_timestamps 0.0 --word_timestamps True --output_dir $WORK 
    json="$WORK/${basename%.mp4}.json"

    while [ ! -s "$json" ]; do
        sleep 0.05
    done

    uv run utils/findstop.py -I $output -O $INBOUND 

    cleaned="$WORK/${basename%.mp4}_clean.wav"
    video="$WORK/$(printf '%03d' "$i")_clip.mp4"
    transition="$WORK/$(printf '%03d' "$y")_transition.mp4"


    ffmpeg -framerate 24 -pattern_type glob -i "$INBOUND/*.png" -c:v libx264 -pix_fmt yuv420p "$WORK/final_video.mp4"
    ffmpeg -i "$WORK/final_video.mp4" -i $cleaned -c:v copy -c:a aac "$video"
    rm $WORK/final_video.mp4

    first=$(find "$WORKING" -maxdepth 1 -type f -name "*.png" | sort | tail -n 1)
    last=$(find "$INBOUND" -maxdepth 1 -type f -name "*.png" | sort | head -n 1)

    transition_duration=0.25

    if [[ -n "$last" && -n "$first" ]]; then

        ffmpeg -framerate 24 -loop 1 -i "$first" \
            -f lavfi -i anullsrc=channel_layout=mono:sample_rate=48000 \
            -shortest \
            -t $transition_duration \
            -c:v libx264 -pix_fmt yuv420p \
            -c:a aac -b:a 128k \
            "$WORK/first.mp4"

        ffmpeg -framerate 24 -loop 1 -i "$last" \
            -f lavfi -i anullsrc=channel_layout=mono:sample_rate=48000 \
            -shortest \
            -t $transition_duration  \
            -c:v libx264 -pix_fmt yuv420p \
            -c:a aac -b:a 128k \
            "$WORK/last.mp4"

        ffmpeg -i $WORK/first.mp4 -i $WORK/last.mp4 \
            -filter_complex "[0]format=yuv420p, gblur=sigma=1[fg]; [1]format=yuv420p, gblur=sigma=1[bg]; [fg][bg]xfade=transition=fade:duration=$transition_duration:offset=0" \
            -c:v libx264 -pix_fmt yuv420p "$transition"

        rm $WORK/first.mp4
        rm $WORK/last.mp4
    fi
    y=$i


    TMP="$WORKING"
    WORKING="$INBOUND"
    INBOUND="$TMP"

    rm -f $INBOUND/*.png
    rm final_video.mp4
done

ls $WORK/*_clip.mp4 $WORK/*_transition.mp4 | sort -V | while read f; do
    echo "file '$(basename "$f")'"
done > $WORK/list.txt

ffmpeg -f concat -safe 0 -i $WORK/list.txt -c copy final.mp4


