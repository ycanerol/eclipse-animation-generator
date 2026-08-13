#!/usr/bin/env bash
#
# build_circle.sh
# Builds the rotating eclipse-circle composite and the N animation frames.
#
# Input : N eclipse frames (tracked shots, sun centered in each frame),
#         named sequentially in SRC_DIR.
# Output: eclipse_circle.png (phase 01 at the bottom, ring clockwise),
#         and N animation frames in OUT_DIR where the sequence shifts
#         one slot counter-clockwise per frame (full loop after N).
#
# CONFIGURATION
#   All values below can be overridden via environment variables.
#   The synthetic-motion defaults match the generated test frames.
#
# USING REAL ECLIPSE FOOTAGE
#   The default moon-motion model derives each frame's moon position
#   from its index with a hardcoded formula. Real eclipse frames do
#   NOT follow that model. Measure the moon offset (dx,dy) relative
#   to the sun center in each source frame and write a
#   moon_positions.txt file (one line per frame):
#       <frame_index> <dx> <dy>
#   When that file exists it takes precedence over the synthetic model.
#   Also set N, SRC_DIR, SIZE and R to match your footage.
#
set -euo pipefail

# --- config (overridable) -------------------------------------------
N="${N:-20}"                     # number of eclipse frames
SRC_DIR="${SRC_DIR:-eclipse_frames}"
SRC_PATTERN="${SRC_PATTERN:-%02d.png}"   # printf-style, 1-based index
OUT_DIR="${OUT_DIR:-circle_frames}"
CIRCLE_OUT="${CIRCLE_OUT:-eclipse_circle.png}"
SIZE="${SIZE:-1600}"             # square canvas side (px)
R="${R:-660}"                    # ring radius (px)

# synthetic moon-motion defaults (only used when moon_positions.txt
# is absent). Geometry is in source-frame pixels.
S="${S:-127.10}"                 # moon-center offset at first/last contact
B="${B:-15.11}"                  # perpendicular offset of the moon path
MAX_FRAME="${MAX_FRAME:-10}"     # frame of eclipse maximum
POSITIONS_FILE="${POSITIONS_FILE:-moon_positions.txt}"

PI='3.141592653589793'
mkdir -p "$OUT_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# moon_offset <j> : echo "dx dy" = moon center relative to sun center
# in source-frame pixels for frame j.
moon_offset() {
  local j="$1"
  if [[ -s "$POSITIONS_FILE" ]]; then
    awk -v j="$j" '$1==j {print $2, $3; exit}' "$POSITIONS_FILE"
    return
  fi
  awk -v j="$j" -v S="$S" -v B="$B" -v MX="$MAX_FRAME" -v N="$N" -v pi="$PI" 'BEGIN{
    if (j<=MX) mx=S*(1-(j-1)/(MX-1)); else mx=-S*((j-MX)/(N-MX));
    print mx, -B
  }'
}

# build <shift f> <outfile> : phase j is placed in slot
# p = (j-1-f) mod N, rotated so its moon faces the ring center.
build() {
  local f="$1" out="$2"
  local args=(-size "${SIZE}x${SIZE}" xc:black)
  for (( j=1; j<=N; j++ )); do
    local p=$(( ((j-1-f)%N+N)%N ))
    local a dx dy th cx cy
    a="$(awk -v p="$p" -v N="$N" 'BEGIN{print 90 + p*360/N}')"
    read dx dy <<< "$(moon_offset "$j")"
    read th cx cy <<< "$(awk -v a="$a" -v dx="$dx" -v dy="$dy" \
                         -v R="$R" -v SZ="$SIZE" -v pi="$PI" 'BEGIN{
      aa=a*pi/180; C=SZ/2
      cx=C+R*cos(aa); cy=C+R*sin(aa)
      b=atan2(dy,dx); g=atan2(-sin(aa),-cos(aa))
      th=(g-b)*180/pi
      printf "%.2f %.0f %.0f", th, cx, cy
    }')"
    local src="$SRC_DIR/$(printf "$SRC_PATTERN" "$j")"
    local r="$TMP/r_${f}_${j}.png"
    magick "$src" -alpha set -background none -rotate "$th" "$r"
    local w h
    read w h <<< "$(magick "$r" -format '%w %h' info:)"
    args+=(-draw "image over $((cx-w/2)),$((cy-h/2)) 0,0 '$r'")
  done
  magick "${args[@]}" "$out"
}

# static reference circle: shift 0 (phase 01 at the bottom)
build 0 "$CIRCLE_OUT"
echo "wrote $CIRCLE_OUT"

# animation frames: one shift per frame = one full counter-clockwise lap
for (( f=0; f<N; f++ )); do
  build "$f" "$(printf "$OUT_DIR/$SRC_PATTERN" $((f+1)))"
done
echo "wrote $N frames to $OUT_DIR/"
