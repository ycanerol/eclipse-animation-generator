import numpy as np
from PIL import Image

W = H = 200
CX = CY = W // 2
SUN_R = 64.0
MOON_R = 64.0
EDGE = 2.5


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def disk_alpha(cx, cy, r, shape):
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    return 1.0 - smoothstep(r - EDGE, r + EDGE, d)


def palette(keys, t):
    keys = sorted(keys)
    pos = [k[0] for k in keys]
    t = np.clip(np.asarray(t, dtype=float), pos[0], pos[-1])
    r = np.interp(t, pos, [k[1][0] for k in keys])
    g = np.interp(t, pos, [k[1][1] for k in keys])
    b = np.interp(t, pos, [k[1][2] for k in keys])
    return np.stack([r, g, b], axis=-1)


def overlap_fraction(d):
    r = SUN_R
    if d <= 0.0:
        return 1.0
    if d >= 2.0 * r:
        return 0.0
    u = d / (2.0 * r)
    area = 2.0 * r * r * np.arccos(u) - (d / 2.0) * np.sqrt(4.0 * r * r - d * d)
    return area / (np.pi * r * r)


lo, hi = 0.0, 2.0 * SUN_R
for _ in range(60):
    mid = (lo + hi) / 2.0
    if overlap_fraction(mid) > 0.85:
        lo = mid
    else:
        hi = mid
B = (lo + hi) / 2.0
S_FAR = np.sqrt((2.0 * SUN_R) ** 2 - B ** 2)

print(f"impact param B={B:.2f}, half-traverse S_FAR={S_FAR:.2f}")

BASE_SUN = [
    (0.00, (255, 253, 242)),
    (0.50, (255, 248, 216)),
    (0.82, (255, 236, 176)),
    (1.00, (255, 216, 132)),
]

SUNSET_SUN = [
    (0.00, (255, 240, 210)),
    (0.45, (255, 205, 130)),
    (0.78, (255, 150, 62)),
    (1.00, (246, 82, 24)),
]

MOON_COLOR = np.array((0, 0, 0), dtype=float)

y, x = np.mgrid[0:W, 0:H]
d2_sun = (x - CX) ** 2 + (y - CY) ** 2
r_norm = np.sqrt(d2_sun) / SUN_R


def moon_x(i):
    if i <= 10:
        return CX + S_FAR * (1.0 - (i - 1) / 9.0)
    return CX - S_FAR * ((i - 10) / 10.0)


for i in range(1, 21):
    mx = moon_x(i)
    d = np.sqrt((mx - CX) ** 2 + B ** 2)
    occ = overlap_fraction(d)

    c = 0.0 if i <= 10 else (i - 10) / 10.0

    sun_mask = disk_alpha(CX, CY, SUN_R, (W, H))
    moon_mask = disk_alpha(mx, CY - B, MOON_R, (W, H))

    sun_col = palette(BASE_SUN, r_norm) * (1.0 - c) + palette(SUNSET_SUN, r_norm) * c

    a = moon_mask + sun_mask * (1.0 - moon_mask)
    rgb = MOON_COLOR * moon_mask[..., None] + sun_col * sun_mask[..., None] * (1.0 - moon_mask[..., None])
    rgb = np.where(a[..., None] > 1e-4, rgb / np.maximum(a[..., None], 1e-4), 0.0)

    rgba = np.dstack([rgb, a * 255.0])
    img = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
    img.save(f"{i:02d}.png")
    print(f"saved {i:02d}.png occ={occ:.1%} c={c:.2f} moon_x={mx:.1f}")
