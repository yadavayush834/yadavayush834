"""Generate assets/night.svg — an animated pixel-art night skyline (deterministic)."""

import os
import random

random.seed(834)
P = 5                  # pixel size
W, H = 172, 52         # grid -> 860 x 260 px
out = []


def run_rects(grid_rows, color, extra=""):
    """Merge horizontal runs of True cells into rects."""
    parts = []
    for y, row in enumerate(grid_rows):
        x = 0
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                parts.append(f'<rect x="{s*P}" y="{y*P}" width="{(x-s)*P}" height="{P}"/>')
            else:
                x += 1
    return f'<g fill="{color}"{extra}>' + "".join(parts) + "</g>"


# ---- sky: banded gradient with ordered dithering between bands ----
bands = ["#07060f", "#0b0a1c", "#120f2b", "#1b1440", "#271a52", "#3a1f5c"]
band_h = 7
bayer = [[0, 2], [3, 1]]
for i, c in enumerate(bands):
    out.append(f'<rect x="0" y="{i*band_h*P}" width="{W*P}" height="{(H - i*band_h)*P}" fill="{c}"/>')
for i in range(1, len(bands)):
    y0 = i * band_h
    rows = [[False] * W for _ in range(H)]
    for y in (y0 - 2, y0 - 1):
        for x in range(W):
            lvl = 1 if y == y0 - 2 else 2
            rows[y][x] = bayer[y % 2][x % 2] < lvl
    out.append(run_rects(rows, bands[i]))

# ---- stars (some twinkle) ----
stars = []
for _ in range(70):
    x, y = random.randrange(W), random.randrange(0, 30)
    if 128 <= x <= 146 and 4 <= y <= 20:
        continue  # keep the moon clear
    col = random.choice(["#ffffff", "#c7d2fe", "#fde68a", "#e9d5ff"])
    if random.random() < 0.45:
        d = round(random.uniform(1.6, 4.2), 1)
        b = round(random.uniform(0, 4), 1)
        stars.append(f'<rect x="{x*P}" y="{y*P}" width="{P}" height="{P}" fill="{col}">'
                     f'<animate attributeName="opacity" values="1;.15;1" dur="{d}s" begin="{b}s" repeatCount="indefinite"/></rect>')
    else:
        stars.append(f'<rect x="{x*P}" y="{y*P}" width="{P}" height="{P}" fill="{col}" opacity="{random.choice([.5,.7,.9])}"/>')
# a few plus-shaped bright stars
for x, y in [(22, 6), (71, 3), (104, 11), (160, 24)]:
    stars.append(f'<g fill="#ffffff"><rect x="{x*P}" y="{(y-1)*P}" width="{P}" height="{3*P}" opacity=".55"/>'
                 f'<rect x="{(x-1)*P}" y="{y*P}" width="{3*P}" height="{P}" opacity=".55"/>'
                 f'<rect x="{x*P}" y="{y*P}" width="{P}" height="{P}"/>'
                 f'<animate attributeName="opacity" values="1;.4;1" dur="3s" begin="{x%3}s" repeatCount="indefinite"/></g>')
out += stars

# ---- crescent moon with glow ----
cx, cy, r = 137, 12, 6
glow = [[False] * W for _ in range(H)]
moon = [[False] * W for _ in range(H)]
shade = [[False] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        d2 = (x - cx) ** 2 + (y - cy) ** 2
        if d2 <= r * r:
            if (x - cx - 3) ** 2 + (y - cy + 2) ** 2 <= (r - 1) ** 2:
                continue  # bite out -> crescent
            moon[y][x] = True
            if (x - cx) + (y - cy) > 3:
                shade[y][x] = True
        elif d2 <= (r + 3) ** 2 and (x + y) % 2 == 0:
            glow[y][x] = True
out.append(run_rects(glow, "#fde68a", ' opacity=".12"'))
out.append(run_rects(moon, "#fef3c7"))
out.append(run_rects(shade, "#fcd34d"))

# ---- shooting star ----
trail = "".join(f'<rect x="{-i*P}" y="{-i*P//2*1}" width="{P}" height="{P}" opacity="{1 - i/7:.2f}"/>' for i in range(7))
out.append(f'<g fill="#ffffff" opacity="0"><g>{trail}</g>'
           f'<animateTransform attributeName="transform" type="translate" values="{40*P},{2*P};{110*P},{20*P}" dur="9s" keyTimes="0;1" '
           f'calcMode="spline" keySplines=".2 .6 .4 1" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;.62;.66;.78;1" dur="9s" repeatCount="indefinite"/></g>')


# ---- skyline layers ----
def skyline(base, min_h, max_h, min_w, max_w, color, windows=None, antenna=False):
    heights = [0] * W
    x = 0
    while x < W:
        w = random.randint(min_w, max_w)
        h = random.randint(min_h, max_h)
        for i in range(x, min(W, x + w)):
            heights[i] = h
        if antenna and random.random() < 0.3 and x + w // 2 < W:
            ax = x + w // 2
            heights[ax] = h + random.randint(2, 4)
        x += w + random.choice([0, 0, 1])
    rows = [[base - heights[x] <= y < base for x in range(W)] for y in range(H)]
    parts = [run_rects(rows, color)]
    if windows:
        lit, flick = [], []
        for x in range(1, W - 1):
            h = heights[x]
            if h < 5:
                continue
            for y in range(base - h + 2, base - 1, 2):
                if x % 2 == 0 and random.random() < 0.28:
                    rect = f'<rect x="{x*P}" y="{y*P}" width="{P}" height="{P}"'
                    if random.random() < 0.12:
                        d = random.randint(4, 11)
                        flick.append(rect + f'><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.45;.5;.8;1" dur="{d}s" begin="{random.randint(0,6)}s" repeatCount="indefinite"/></rect>')
                    else:
                        lit.append(rect + "/>")
        parts.append(f'<g fill="{windows}">' + "".join(lit) + "".join(flick) + "</g>")
    return "".join(parts)


out.append(skyline(H, 10, 22, 4, 9, "#1e1638"))
out.append(skyline(H, 6, 16, 5, 11, "#120d24", windows="#fbbf24", antenna=True))
out.append(skyline(H, 2, 8, 6, 14, "#07050f", windows="#f472b6"))

# blinking antenna lights on the tallest mid-layer towers
for x, y in [(31, 30), (88, 33), (149, 31)]:
    out.append(f'<rect x="{x*P}" y="{y*P}" width="{P}" height="{P}" fill="#ef4444">'
               f'<animate attributeName="opacity" values="1;1;.1;.1" keyTimes="0;.5;.5;1" dur="1.6s" begin="{x%4*.3:.1f}s" repeatCount="indefinite"/></rect>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W*P} {H*P}" width="{W*P}" height="{H*P}" '
       f'shape-rendering="crispEdges" role="img" aria-label="Pixel art night skyline">'
       f'<clipPath id="r"><rect width="{W*P}" height="{H*P}" rx="12"/></clipPath><g clip-path="url(#r)">'
       + "".join(out) + "</g></svg>\n")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(root, "assets", "night.svg"), "w") as f:
    f.write(svg)
print(len(svg), "bytes")
