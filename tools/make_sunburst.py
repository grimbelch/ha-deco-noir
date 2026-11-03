"""Generate the Deco Noir sunburst/fan background SVG (champagne)."""
import math, pathlib

GOLD = "201,164,76"
W, H = 1600, 2000
cx, cy = W / 2, -60
out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMin slice">')
out.append('<defs><linearGradient id="r" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="rgb({GOLD})" stop-opacity=".30"/>'
           f'<stop offset=".75" stop-color="rgb({GOLD})" stop-opacity="0"/></linearGradient></defs>')
out.append(f'<rect width="{W}" height="{H}" fill="none"/>')
# rays
out.append('<g stroke="url(#r)" stroke-width="1.2">')
for i in range(41):
    a = math.pi * (0.05 + 0.90 * i / 40)
    x1, y1 = cx + math.cos(a) * 320, cy + math.sin(a) * 320
    x2, y2 = cx + math.cos(a) * 2200, cy + math.sin(a) * 2200
    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
out.append('</g>')
# halo rings
out.append(f'<g fill="none" stroke="rgb({GOLD})" stroke-opacity=".14">')
for r in (310, 322, 540, 720):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')
out.append('</g>')
# fans along the bottom
out.append(f'<g fill="none" stroke="rgb({GOLD})" stroke-opacity=".10">')
for fx in (200, W / 2, W - 200):
    fy = H
    for r in range(70, 391, 50):
        out.append(f'<path d="M{fx - r} {fy} A{r} {r} 0 0 1 {fx + r} {fy}"/>')
    for k in range(1, 10):
        t = math.pi * k / 10
        out.append(f'<line x1="{fx}" y1="{fy}" x2="{fx - math.cos(t) * 390:.1f}" y2="{fy - math.sin(t) * 390:.1f}"/>')
out.append('</g>')
# pinstripe borders
out.append(f'<g stroke="rgb({GOLD})" stroke-opacity=".09">')
for x in (70, 86, W - 86, W - 70):
    out.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
out.append('</g></svg>')
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "deco" / "sunburst.svg"
p.write_text("\n".join(out), encoding="utf-8")
print(p, p.stat().st_size, "bytes")
