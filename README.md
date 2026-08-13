# Eclipse Circle Animation

Turns a sequence of partial-solar-eclipse frames into a rotating "carousel"
animation: each frame is placed on a ring (occluded side facing the center,
solar crescent facing out) and the whole sequence orbits the ring once per loop.

## Scripts

- `build_circle.sh` — rotates + arranges frames, writes `eclipse_circle.png` and
  `N` animation frames.
- `encode_animation.sh` — encodes those frames into MP4 + looping GIF.

Requires ImageMagick (`magick`) and `ffmpeg`.

## Input requirements

- **Format**: PNG (RGBA with transparent background is cleanest). Opaque
  photos also work, but the full frame rectangle (sky, etc.) will be visible
  on the black canvas.
- **Naming**: sequential, 1-based, zero-padded, e.g. `01.png`, `02.png`, ...
  Default pattern `%02d.png`; change `SRC_PATTERN` if needed.
- **Size**: any; frames should be square with the sun centered in each
  (tracked shots). The ring radius (`R`) and canvas (`SIZE`) are in pixels
  of the canvas, not the source frames.

## Moon positions (required for real footage)

Real eclipse frames need one measured line per frame in `moon_positions.txt`:

```
<frame_index> <dx> <dy>
```

where `(dx, dy)` is the moon center relative to the sun center in that frame's
pixels (the direction is what matters). Without this file, the script falls
back to a synthetic model meant only for the bundled test frames.

## Usage

```sh
./build_circle.sh          # default: reads eclipse_frames/01..20.png
./encode_animation.sh      # default: circle_frames/01..20.png -> mp4 + gif
```

## Parameters (set via environment variables)

| Variable        | Default            | Purpose                        |
|-----------------|--------------------|--------------------------------|
| `N`             | `20`               | number of frames               |
| `SRC_DIR`       | `eclipse_frames`   | input frame directory          |
| `SRC_PATTERN`   | `%02d.png`         | input frame name pattern       |
| `OUT_DIR`       | `circle_frames`    | animation frame output dir     |
| `CIRCLE_OUT`    | `eclipse_circle.png` | static ring image name       |
| `SIZE`          | `1600`             | square canvas side (px)        |
| `R`             | `660`              | ring radius (px)               |
| `POSITIONS_FILE`| `moon_positions.txt` | measured moon offsets        |
| `S`/`B`/`MAX_FRAME` | `127.10`/`15.11`/`10` | synthetic-model only     |
| `FRAMES_DIR`    | `circle_frames`    | encoder input dir              |
| `FRAME_PATTERN` | `%02d.png`         | encoder frame name pattern     |
| `FPS`           | `10`               | animation frames per second    |
| `OUT_MP4`/`OUT_GIF` | `solar_eclipse_circle.mp4/.gif` | outputs |

### Examples

```sh
# 60 eclipse photos named frame_001.png..frame_060.png, bigger ring
N=60 SRC_DIR="eclipse_photos" SRC_PATTERN="frame_%03d.png" \
SIZE=2160 R=980 ./build_circle.sh

# slower 2s loop for the same 20 frames
FPS=5 ./encode_animation.sh

# custom output names
OUT_MP4=my_eclipse.mp4 OUT_GIF=my_eclipse.gif ./encode_animation.sh
```

## Loop notes

The animation frames step the starting phase one slot counter-clockwise per
frame, so `N` frames complete exactly one lap (frame `N` flows into frame `1`).
