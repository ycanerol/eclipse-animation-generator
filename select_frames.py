import numpy as np
from PIL import Image
import glob, math, os

from measure_all import analyze, RAW, load_gray

TARGET = int(os.environ.get("TARGET", "30"))
OUT_DIR = os.environ.get("OUT_DIR", "2017_partial_eclipse_mit/selected")
MEAS_SCALE = 0.5                      # measure_all analyzes at this scale
EXPORT_SCALE = float(os.environ.get("SCALE", "0.25"))   # exported frame scale
RESID_MAX = float(os.environ.get("RESID_MAX", "12"))
OUT_W, OUT_H = int(1920 * EXPORT_SCALE), int(1080 * EXPORT_SCALE)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def radial_alpha(h, w, cx, cy, R):
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return smoothstep(2.2 * R, 1.1 * R, r)  # 1 inside 1.1R, fades to 0 at 2.2R


def main():
    results = []
    for idx in range(len(RAW)):
        a = analyze(RAW[idx])
        if a is not None and a["moon_dir"] is not None:
            if a["resid"] < RESID_MAX and 0.20 < a["frac"] < 0.80:
                results.append((idx, a))

    results.sort(key=lambda x: x[0])
    idxs = [r[0] for r in results]
    lo, hi = idxs[0], idxs[-1]
    min_gap = float(os.environ.get("GAP", str((hi - lo) / (TARGET - 1))))
    picked = []
    last = -1e9
    for idx, a in results:
        if idx - last >= min_gap:
            picked.append((idx, a))
            last = idx
    print(f"reliable: {len(results)}, picked: {len(picked)} (gap ~{min_gap:.1f})")

    os.makedirs(OUT_DIR, exist_ok=True)
    kscale = EXPORT_SCALE / MEAS_SCALE
    pos = []
    for k, (idx, a) in enumerate(picked, 1):
        g = load_gray(RAW[idx], EXPORT_SCALE)
        h, w = g.shape
        rgb = np.asarray(Image.open(RAW[idx]).convert("RGB").resize((w, h), Image.BILINEAR)).astype(float)
        cxs, cys, rs = a["cx"] * kscale, a["cy"] * kscale, a["r"] * kscale
        alpha = radial_alpha(h, w, cxs, cys, rs)
        rgba = np.dstack([rgb, alpha * 255.0])
        # translate so the sun center sits at the frame center (no cropping)
        dy = int(round(h / 2 - cys))
        dx = int(round(w / 2 - cxs))
        rgba = np.roll(rgba, dy, axis=0)
        rgba = np.roll(rgba, dx, axis=1)
        img = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
        img.save(os.path.join(OUT_DIR, f"{k:02d}.png"))
        md = a["moon_dir"]
        pos.append((k, 100 * math.cos(math.radians(md)), 100 * math.sin(math.radians(md))))
        print(f"  {k:02d}.png <- video frame {idx+1}  moon_dir={md:5.1f}")

    with open("2017_partial_eclipse_mit/moon_positions.txt", "w") as f:
        for j, dx, dy in pos:
            f.write(f"{j} {dx:.3f} {dy:.3f}\n")
    print(f"wrote {len(pos)} frames to {OUT_DIR}/ and moon_positions.txt")


if __name__ == "__main__":
    main()
