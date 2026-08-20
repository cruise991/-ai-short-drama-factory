#!/bin/bash
set -e

# Config
API_KEY="${AGNES_API_KEY:-""}"
EPISODE_DIR="projects/paperai-series/episode-01"
ASSETS_DIR="$EPISODE_DIR/02_raw_assets"
FINAL_DIR="$EPISODE_DIR/04_final_output"
OUT_DIR="../out"

mkdir -p "$ASSETS_DIR" "$FINAL_DIR" "$OUT_DIR"

echo "================================================="
echo "[Production Dept] Starting True API Pipeline..."
echo "================================================="

# SHOT 1
echo ">> Generating Image 1 via Agnes API..."
PROMPT_1="A cinematic shot inside a dimly lit modern laboratory at night. Piles of academic papers are stacked on the desk. A middle-aged man in a suit arrogantly picks up a hard drive from the desk, smirking. A young woman with glasses looks up at him with a shocked and angry expression. Dramatic cold lighting, highly detailed, 8k resolution. --seed 10245 --quality highly_detailed, consistent_face"

IMG_RES_1=$(/usr/bin/curl -s -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "'"$PROMPT_1"'",
    "size": "1024x768",
    "extra_body": {"response_format": "url"}
  }')

IMG_URL_1=$(echo "$IMG_RES_1" | grep -o '"url":"[^"]*' | cut -d'"' -f4)

if [ -z "$IMG_URL_1" ]; then
    echo "Fallback failed"
fi

echo "   -> URL: $IMG_URL_1"
/usr/bin/curl -s -o "$ASSETS_DIR/shot_01.png" "$IMG_URL_1"

echo ">> Generating Video 1 via Agnes API (Img2Vid)..."
VID_RES_1=$(/usr/bin/curl -s -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "The man grabs the drive slowly. Camera pans.",
    "image": "'"$IMG_URL_1"'",
    "num_frames": 121,
    "frame_rate": 24
  }')

TASK_ID_1=$(echo "$VID_RES_1" | grep -o '"video_id":"[^"]*' | cut -d'"' -f4)
if [ -z "$TASK_ID_1" ]; then
    TASK_ID_1=$(echo "$VID_RES_1" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)
fi
echo "   -> Task ID: $TASK_ID_1"

# SHOT 2
echo ">> Generating Image 2 via Agnes API..."
PROMPT_2="A bright, high-end corporate boardroom with large windows. A middle-aged man stands at the podium looking panicked and sweating. A young confident woman walks through the door holding a smartphone displaying a sleek AI interface. A large screen behind them shows a glowing, complex academic knowledge graph. Cinematic lighting, dramatic entrance, highly detailed, photorealistic. --seed 10245 --quality highly_detailed, consistent_face"

IMG_RES_2=$(/usr/bin/curl -s -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "'"$PROMPT_2"'",
    "size": "1024x768",
    "extra_body": {"response_format": "url"}
  }')

IMG_URL_2=$(echo "$IMG_RES_2" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
echo "   -> URL: $IMG_URL_2"
/usr/bin/curl -s -o "$ASSETS_DIR/shot_02.png" "$IMG_URL_2"

echo ">> Generating Video 2 via Agnes API (Img2Vid)..."
VID_RES_2=$(/usr/bin/curl -s -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "The woman walks forward confidently. Slow motion.",
    "image": "'"$IMG_URL_2"'",
    "num_frames": 121,
    "frame_rate": 24
  }')

TASK_ID_2=$(echo "$VID_RES_2" | grep -o '"video_id":"[^"]*' | cut -d'"' -f4)
if [ -z "$TASK_ID_2" ]; then
    TASK_ID_2=$(echo "$VID_RES_2" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)
fi
echo "   -> Task ID: $TASK_ID_2"


echo ">> Polling for Video 1..."
while true; do
  STATUS_RES=$(/usr/bin/curl -s -H "Authorization: Bearer $API_KEY" "https://apihub.agnes-ai.com/agnesapi?video_id=$TASK_ID_1")
  STATUS=$(echo "$STATUS_RES" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  echo "   -> Status: $STATUS"
  if [ "$STATUS" == "completed" ]; then
    VID_URL_1=$(echo "$STATUS_RES" | grep -o '"remixed_from_video_id":"[^"]*' | cut -d'"' -f4)
    /usr/bin/curl -s -o "$ASSETS_DIR/shot_01.mp4" "$VID_URL_1"
    echo "   -> Downloaded Shot 1"
    break
  fi
  if [ "$STATUS" == "failed" ]; then
    echo "Shot 1 failed"
    exit 1
  fi
  sleep 15
done

echo ">> Polling for Video 2..."
while true; do
  STATUS_RES=$(/usr/bin/curl -s -H "Authorization: Bearer $API_KEY" "https://apihub.agnes-ai.com/agnesapi?video_id=$TASK_ID_2")
  STATUS=$(echo "$STATUS_RES" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  echo "   -> Status: $STATUS"
  if [ "$STATUS" == "completed" ]; then
    VID_URL_2=$(echo "$STATUS_RES" | grep -o '"remixed_from_video_id":"[^"]*' | cut -d'"' -f4)
    /usr/bin/curl -s -o "$ASSETS_DIR/shot_02.mp4" "$VID_URL_2"
    echo "   -> Downloaded Shot 2"
    break
  fi
  if [ "$STATUS" == "failed" ]; then
    echo "Shot 2 failed"
    exit 1
  fi
  sleep 15
done


echo "================================================="
echo "[Post-Production Dept] Starting Final Assembly..."
echo "================================================="

# Audio TTS
echo ">> Generating TTS Audio using macOS Ting-Ting..."
say -v Ting-Ting -o "$ASSETS_DIR/shot_01_audio.aiff" "唐导，这个月第四个课题了。代码、数据、论文，我用 Agent 十分钟全搞定，为什么不让我过？"
say -v Ting-Ting -o "$ASSETS_DIR/shot_02_audio.aiff" "快还有错？！别人还在一行行啃文献，我的 AI 已经跑完了！这都什么时代了，您还在用慢办法？"

# Merge
echo ">> Merging Video and Audio for Shot 1..."
ffmpeg -y -i "$ASSETS_DIR/shot_01.mp4" -i "$ASSETS_DIR/shot_01_audio.aiff" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "$FINAL_DIR/shot_01_final.mp4" </dev/null

echo ">> Merging Video and Audio for Shot 2..."
ffmpeg -y -i "$ASSETS_DIR/shot_02.mp4" -i "$ASSETS_DIR/shot_02_audio.aiff" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "$FINAL_DIR/shot_02_final.mp4" </dev/null

# Concat
echo ">> Concatenating Final Master..."
cat << 'EOF' > "$FINAL_DIR/concat_list.txt"
file 'shot_01_final.mp4'
file 'shot_02_final.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i "$FINAL_DIR/concat_list.txt" -c copy "$FINAL_DIR/episode-01_master.mp4" </dev/null

echo ">> Copying to global out folder..."
cp "$FINAL_DIR/episode-01_master.mp4" "$OUT_DIR/episode-01_master_final.mp4"
echo "DONE! Final video at $OUT_DIR/episode-01_master_final.mp4"
