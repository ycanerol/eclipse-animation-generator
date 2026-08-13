#!/usr/bin/env bash
#
# encode_animation.sh
# Encodes the animation frames from OUT_DIR (produced by build_circle.sh)
# into an MP4 and an infinitely-looping GIF.
#
# CONFIGURATION (overridable via environment variables)
#   FRAMES_DIR  - directory containing the animation frames
#   FRAME_PATTERN - printf-style frame name pattern (1-based)
#   FPS         - frames per second (default 10 -> 2s loop for 20 frames)
#   OUT_MP4 / OUT_GIF - output file names
#
set -euo pipefail

FRAMES_DIR="${FRAMES_DIR:-circle_frames}"
FRAME_PATTERN="${FRAME_PATTERN:-%02d.png}"
FPS="${FPS:-10}"
OUT_MP4="${OUT_MP4:-solar_eclipse_circle.mp4}"
OUT_GIF="${OUT_GIF:-solar_eclipse_circle.gif}"

# MP4 (H.264, yuv420p for broad player compatibility)
ffmpeg -y -framerate "$FPS" -i "$FRAMES_DIR/$FRAME_PATTERN" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$OUT_MP4"

# GIF (global palette optimized over all frames, infinite loop)
ffmpeg -y -framerate "$FPS" -i "$FRAMES_DIR/$FRAME_PATTERN" \
  -vf "split[s0][s1];[s0]palettegen=stats_mode=full[p];[s1][p]paletteuse=dither=bayer" \
  -loop 0 "$OUT_GIF"

echo "wrote $OUT_MP4 and $OUT_GIF"
