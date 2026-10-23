#!/usr/bin/env bash
# Assemble the final launch video from the live Playwright capture.
#
# Source capture: /tmp/opencode/video_raw/demo_raw.webm
# Raw duration:   50.24 s
# Trim window:    6.40 s -> 49.00 s (hero through circuit hold)
# Title card:     4.0 s
# End card:       6.5 s
# Final duration: 53.1 s
#
# Usage:
#   ./scripts/assemble_video.sh [path-to-raw.webm]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="${1:-/tmp/opencode/video_raw/demo_raw.webm}"
OUT="$ROOT/video/Quantum_Lab_Launch.mp4"
TRIM_START=6.4
TRIM_END=49.0
TITLE_SECONDS=4.0
END_SECONDS=6.5
FPS=25

if [[ ! -f "$RAW" ]]; then
  echo "missing raw capture: $RAW" >&2
  echo "record one with: python scripts/record_demo.py" >&2
  exit 1
fi

CONTENT_SECONDS=$(awk -v a="$TRIM_START" -v b="$TRIM_END" 'BEGIN { printf "%.3f", b - a }')
FADE_START=$(awk -v c="$CONTENT_SECONDS" 'BEGIN { printf "%.3f", c - 0.5 }')
TOTAL_SECONDS=$(awk -v t="$TITLE_SECONDS" -v c="$CONTENT_SECONDS" -v e="$END_SECONDS" 'BEGIN { printf "%.3f", t + c + e }')

echo "title ${TITLE_SECONDS}s + content ${CONTENT_SECONDS}s + end ${END_SECONDS}s = ${TOTAL_SECONDS}s"

ffmpeg -y -hide_banner -loglevel warning -stats \
  -loop 1 -t "$TITLE_SECONDS" -i "$ROOT/video/title_card_1080.png" \
  -i "$RAW" \
  -loop 1 -t "$END_SECONDS" -i "$ROOT/video/end_card_1080.png" \
  -filter_complex "\
    [0:v]fps=${FPS},scale=1920:1080:flags=lanczos,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS,\
fade=t=out:st=3.5:d=0.5:color=0xF7F7F5[t]; \
    [1:v]trim=start=${TRIM_START}:end=${TRIM_END},setpts=PTS-STARTPTS,fps=${FPS},\
scale=1920:1080:flags=lanczos,format=yuv420p,settb=AVTB,\
fade=t=in:st=0:d=0.3,fade=t=out:st=${FADE_START}:d=0.5:color=0x161616[c]; \
    [2:v]fps=${FPS},scale=1920:1080:flags=lanczos,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS,\
fade=t=in:st=0:d=0.4[e]; \
    [t][c][e]concat=n=3:v=1:a=0[out]" \
  -map "[out]" -r "$FPS" -pix_fmt yuv420p \
  -c:v libx264 -preset medium -crf 18 \
  -movflags +faststart \
  -metadata title="Quantum Lab — validated H2 VQE workbench" \
  -metadata artist="Abdelhakim Baalla" \
  -metadata comment="Live local capture; no hardware execution." \
  "$OUT"

ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
