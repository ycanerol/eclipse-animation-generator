import numpy as np
from PIL import Image
import glob, math, os, sys

from measure_moon import analyze, RAW

STEP = int(os.environ.get("STEP", "20"))
OUT_DIR = os.environ.get("OUT_DIR", "2017_partial_eclipse_mit/samples")
TARGET = int(os.environ.get("TARGET", "400"))
CROP_MULT = float(os.environ.get("CROP_MULT", "3.0"))

os.makedirs(OUT_DIR, exist_ok=True)
pos = []
rows = []
k = 0
for idx in range(0, len(RAW), STEP):
    vid = idx + 1
    res = analyze(RAW[idx])
    if res is None or res["moon_dir"] is None:
        rows.append((vid, None))
        continue
    cx, cy, r, md = res["cx"], res["cy"], res["r"], res["moon_dir"]
    side = int(CROP_MULT * r)
    x0, y0 = int(cx - side / 2), int(cy - side / 2)
    img = Image.open(RAW[idx]).convert("RGB")
    w, h = img.size
    # pad crop region with black where it falls outside the frame
    pad = Image.new("RGB", (side, side), (0, 0, 0))
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x0 + side), min(h, y0 + side)
    patch = img.crop((sx0, sy0, sx1, sy1))
    pad.paste(patch, (sx0 - x0, sy0 - y0))
    pad = pad.resize((TARGET, TARGET), Image.LANCZOS)
    k += 1
    name = f"{k:02d}.png"
    pad.save(os.path.join(OUT_DIR, name))
    mag = 100.0
    dx = mag * math.cos(math.radians(md))
    dy = mag * math.sin(math.radians(md))
    pos.append((k, dx, dy))
    rows.append((vid, (name, md)))

with open("2017_partial_eclipse_mit/moon_positions.txt", "w") as f:
    for j, dx, dy in pos:
        f.write(f"{j} {dx:.3f} {dy:.3f}\n")

print(f"sampled every {STEP}th frame -> {len(RAW)} frames scanned, {k} usable")
for vid, info in rows:
    if info:
        print(f"  video frame {vid:4d} -> samples/{info[0]}  moon_dir={info[1]:.0f}")
    else:
        print(f"  video frame {vid:4d} -> (skip: no detectable moon)")
