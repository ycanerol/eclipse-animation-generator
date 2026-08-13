import numpy as np
from PIL import Image
import glob, math

RAW = sorted(glob.glob("2017_partial_eclipse_mit/raw/f_*.png"))


def analyze(path):
    g = np.asarray(Image.open(path).convert("L")).astype(float)
    mx = float(g.max())
    if mx < 60:
        return None
    mask = (g > 0.85 * mx)
    mask[850:, :500] = False
    ys, xs = np.where(mask)
    if len(xs) < 50:
        return None
    cx, cy = xs.mean(), ys.mean()
    r = math.sqrt(len(xs) / math.pi)
    # angular bins around sun center
    yy, xx = np.mgrid[0:1080, 0:1920]
    ddx, ddy = xx - cx, yy - cy
    dist = np.sqrt(ddx ** 2 + ddy ** 2)
    ang = np.degrees(np.arctan2(ddy, ddx)) % 360
    ring = (dist >= 0.55 * r) & (dist <= 0.95 * r)
    gring = g[ring]
    aring = ang[ring]
    bins = np.arange(0, 361, 4)
    idx = np.digitize(aring, bins) - 1
    idx = np.clip(idx, 0, 89)
    mean = np.full(90, np.nan)
    for b in range(90):
        sel = idx == b
        if sel.sum() > 3:
            mean[b] = gring[sel].mean()
    # find bright arc (crescent). bright = mean > 0.55*mx
    bright = ~np.isnan(mean) & (mean > 0.55 * mx)
    if bright.sum() == 0:
        return dict(cx=cx, cy=cy, r=r, moon_dir=None, frac=0.0, mx=mx)
    # contiguous bright runs; crescent = largest run
    runs = []
    n = len(bright)
    i = 0
    while i < n:
        if bright[i]:
            j = i
            while j < n and bright[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    if len(runs) > 1 and bright[0] and bright[-1]:
        # merge the two runs that touch across the 0/360 boundary
        merged = (runs[-1][0] - n, runs[0][1])
        runs = [merged] + runs[1:-1]
    if not runs:
        return dict(cx=cx, cy=cy, r=r, moon_dir=None, frac=0.0, mx=mx)
    s, e = max(runs, key=lambda r: r[1] - r[0])
    arc_len = e - s
    ctr_deg = ((s + e) / 2.0) % n * 4
    frac = arc_len / 90.0
    if frac > 0.85:
        # no meaningful bite (crescent wraps most of the sun)
        return dict(cx=cx, cy=cy, r=r, moon_dir=None, frac=frac, mx=mx)
    moon_dir = (ctr_deg + 180) % 360  # opposite the crescent
    return dict(cx=cx, cy=cy, r=r, moon_dir=moon_dir, frac=frac, mx=mx)


def main():
    lo, hi = 1, len(RAW)
    if len(sys.argv) > 2:
        lo, hi = int(sys.argv[1]), int(sys.argv[2])
    for idx in range(lo - 1, hi):
        res = analyze(RAW[idx])
        if res is None or res["moon_dir"] is None:
            print(f"{idx+1:4d}: -")
            continue
        print(f"{idx+1:4d}: sun=({res['cx']:.0f},{res['cy']:.0f}) r={res['r']:.0f} "
              f"moon_dir={res['moon_dir']:6.1f} crescent_frac={res['frac']:.2f}")


if __name__ == "__main__":
    import sys
    main()
