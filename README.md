# Podcast
Generate podcasts from RSS feeds

For defauult LTX settings with local wangp need the following lora

```
hf download DeepBeepMeep/LTX-2 id-lora-celebvhq-ltx2.3.safetensors --local-dir .
```

Copy this lora into Wan2GP/loras/ltx2 folder

```
./build_video.sh 0 # Global news
./build_video.sh 1 # Gaming news
./build_video.sh 2 # Science and Technology news
```

