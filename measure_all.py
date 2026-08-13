import numpy as np
from PIL import Image
import glob, math

RAW = sorted(glob.glob("2017_partial_eclipse_mit/raw/f_*.png"))


def load_gray(path, scale=0.5):
    img = Image.open(path).convert("L")
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BILINEAR)
    return np.asarray(img).astype(float)


def sun_circle(g):
    """Robust sun-disk circle fit from the bright region's outer limb."""
    mx = float(g.max())
    if mx < 60:
        return None
    thr = 0.45 * mx
    b = g > thr
    if b.sum() < 200:
        return None
    # seed from bright centroid
    ys, xs = np.where(b)
    seed_cx, seed_cy = xs.mean(), ys.mean()
    seed_r = math.sqrt(b.sum() / math.pi)
    # boundary pixels
    e = np.zeros_like(b)
    e[1:-1, 1:-1] = b[1:-1, 1:-1] & ~(
        b[:-2, 1:-1] & b[2:, 1:-1] & b[1:-1, :-2] & b[1:-1, 2:]
    )
    ey, ex = np.where(e)
    if len(ex) < 30:
        return None
    pts = np.stack([ex, ey], axis=1).astype(float)
    cx, cy, R = seed_cx, seed_cy, seed_r
    resids = []
    for _ in range(8):
        d = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
        good = np.abs(d - R) < 0.30 * R
        if good.sum() < 30:
            break
        P = pts[good]
        A = np.stack([P[:, 0], P[:, 1], np.ones(len(P))], axis=1)
        v = P[:, 0] ** 2 + P[:, 1] ** 2
        coef, *_ = np.linalg.lstsq(A, v, rcond=None)
        a, b_, c = coef
        cx, cy = a / 2, b_ / 2
        R = math.sqrt(max(1e-6, c + cx * cx + cy * cy))
    if not (40 < R < 300):
        return None
    # residual: typical deviation of inliers
    d = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    inl = np.abs(d - R) < 0.30 * R
    resid = float(np.abs(d[inl] - R).mean()) if inl.sum() else 1e9
    return dict(cx=cx, cy=cy, r=R, resid=resid, n_inl=int(inl.sum()), mx=mx)


def moon_dir(g, res):
    """Angular dark-sector method around fitted sun center -> moon direction."""
    cx, cy, R = res["cx"], res["cy"], res["r"]
    mx = res["mx"]
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    ddx, ddy = xx - cx, yy - cy
    dist = np.sqrt(ddx ** 2 + ddy ** 2)
    ang = np.degrees(np.arctan2(ddy, ddx)) % 360
    ring = (dist >= 0.45 * R) & (dist <= 0.90 * R)
    gring = g[ring]
    aring = ang[ring]
    bins = np.arange(0, 361, 6)
    idx = np.clip(np.digitize(aring, bins) - 1, 0, 59)
    mean = np.full(60, np.nan)
    for b in range(60):
        sel = idx == b
        if sel.sum() > 4:
            mean[b] = gring[sel].mean()
    bright = ~np.isnan(mean) & (mean > 0.50 * mx)
    n = len(bright)
    if bright.sum() == 0:
        return None
    runs = []
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
        runs = [(runs[-1][0] - n, runs[0][1])] + runs[1:-1]
    if not runs:
        return None
    s, e = max(runs, key=lambda r: r[1] - r[0])
    arc_len = e - s
    frac = arc_len / n
    # direction reliability
    if not (0.15 < frac < 0.88):
        return None
    # require the dark sector to be genuinely dark (real bite)
    darkbins = ~bright & ~np.isnan(mean)
    if darkbins.sum() < 6:
        return None
    dark_mean = mean[darkbins].mean()
    if dark_mean > 0.30 * mx:
        return None
    ctr_deg = ((s + e) / 2.0) % n * (360 / n)
    moon = (ctr_deg + 180) % 360
    return dict(moon_dir=moon, frac=frac, dark_mean=dark_mean)


def analyze(path, scale=0.5):
    g = load_gray(path, scale)
    res = sun_circle(g)
    if res is None:
        return None
    md = moon_dir(g, res)
    if md is None:
        return dict(res, moon_dir=None)
    return dict(res, **md)


if __name__ == "__main__":
    import sys
    lo, hi = 1, len(RAW)
    if len(sys.argv) > 2:
        lo, hi = int(sys.argv[1]), int(sys.argv[2])
    for idx in range(lo - 1, hi):
        a = analyze(RAW[idx])
        if a is None or a["moon_dir"] is None:
            print(f"{idx+1:4d}: -")
            continue
        print(f"{idx+1:4d}: sun=({a['cx']:.0f},{a['cy']:.0f}) r={a['r']:.0f} "
              f"resid={a['resid']:.1f} moon={a['moon_dir']:5.1f} frac={a['frac']:.2f}")
