"""Generate Deco Noir floor plan SVGs (main / upper / lower) and marker positions.

Coordinates are in the pixel space of the original measured floor plan sketch,
so rooms and device markers share one coordinate system. Each floor gets its own
viewBox; marker positions are emitted as percentages for picture-elements.

Fonts (Poiret One, Josefin Sans; SIL OFL) are embedded as base64 so the SVG renders
correctly when loaded as an <img>.
"""
import base64, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "www" / "deco"

# Palettes: one set of floor plans per theme so maps never clash with the page.
#   gold  -> Deco Noir / Deco Noir Lite (dark page)   files: floor_<key>.svg, glow_<entity>.svg
#   cog   -> Cogitator (green phosphor, dark page)    files: floor_<key>_cog.svg, glow_cog_<entity>.svg
#   sea   -> Les Saisons (ivory page, terracotta)     files: floor_<key>_sea.svg, glow_sea_<entity>.svg
PALETTES = {
    "gold": dict(suffix="", glow_prefix="glow_", main="#C9A44C", hi="#E6CF9A", text="#EDE6D6", wall_rgb="201,164,76",
                 wall_fill=".035", out_fill=".02", wall_op=".55", glow_rgb=None, name_font="'Poiret One',sans-serif",
                 dim_font="'Josefin Sans',sans-serif", name_size="13px", name_sp="2.2px", sm_size="9.5px", sm_sp="1.6px",
                 title_size="13px", title_sp="4px", dim_op=".42", italic="normal", out_op=".45", stairs_op=".45", fire_op=".7", dim_size="7.5px", dim_sp="1.4px",
                 fonts=lambda: font_face("Poiret One", "poiret.woff2") + font_face("Josefin Sans", "josefin.woff2")),
    "cog": dict(suffix="_cog", glow_prefix="glow_cog_", main="#58e284", hi="#befacc", text="#befacc", wall_rgb="88,226,132",
                wall_fill=".05", out_fill=".025", wall_op=".7", glow_rgb="110,255,165", name_font="'Cog Data','Courier New',monospace",
                dim_font="'Cog Data','Courier New',monospace", name_size="12px", name_sp="1.4px", sm_size="9px", sm_sp="1px",
                title_size="12px", title_sp="3.4px", dim_op=".6", italic="normal", out_op=".55", stairs_op=".5", fire_op=".8", dim_size="8px", dim_sp="1.2px",
                fonts=lambda: ttf_face("Cog Data", "cog-data-sub.ttf")),
    "sea": dict(suffix="_sea", glow_prefix="glow_sea_", main="#8b5b36", hi="#633e25", text="#49311f", wall_rgb="139,91,54",
                wall_fill=".07", out_fill=".04", wall_op=".8", glow_rgb="255,178,72", name_font="'Cormorant Garamond',Georgia,serif",
                dim_font="'Cormorant Garamond',Georgia,serif", name_size="15px", name_sp="1.2px", sm_size="11.5px", sm_sp="1px",
                title_size="15px", title_sp="3px", dim_op=".75", italic="italic", out_op=".6", stairs_op=".55", fire_op=".85", dim_size="10px", dim_sp="1px",
                fonts=lambda: ttf_face("Cormorant Garamond", "seasons-display-sub.ttf")),
}
PAL = PALETTES["gold"]   # set per variant by main_()


def font_face(name, file):
    b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


def ttf_face(name, file):
    b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{b64}) format('truetype');}}"


def style_css(p):
    g, hi, tx = p["main"], p["hi"], p["text"]
    return (p["fonts"]() + f"""
.wall{{fill:rgba({p["wall_rgb"]},{p["wall_fill"]});stroke:{g};stroke-opacity:{p["wall_op"]};stroke-width:1.3}}
.ext{{fill:none;stroke:{g};stroke-width:3.2;stroke-linejoin:miter}}
.ext2{{fill:none;stroke:{g};stroke-opacity:.35;stroke-width:1;stroke-linejoin:miter}}
.out{{fill:rgba({p["wall_rgb"]},{p["out_fill"]});stroke:{g};stroke-opacity:{p["out_op"]};stroke-width:1.1;stroke-dasharray:5 4}}
.stairs{{stroke:{g};stroke-opacity:{p["stairs_op"]};stroke-width:1}}
.fire{{fill:url(#hatch);stroke:{g};stroke-opacity:{p["fire_op"]};stroke-width:1}}
.name{{font-family:{p["name_font"]};font-style:{p["italic"]};fill:{hi};font-size:{p["name_size"]};letter-spacing:{p["name_sp"]};text-anchor:middle}}
.name.sm{{font-size:{p["sm_size"]};letter-spacing:{p["sm_sp"]}}}
.dim{{font-family:{p["dim_font"]};font-style:{p["italic"]};fill:{tx};fill-opacity:{p["dim_op"]};font-size:{p["dim_size"]};letter-spacing:{p["dim_sp"]};text-anchor:middle}}
.title{{font-family:{p["name_font"]};font-style:{p["italic"]};fill:{hi};font-size:{p["title_size"]};letter-spacing:{p["title_sp"]}}}
.orn{{fill:{g}}}
""")


def defs_xml(p):
    return (f'<defs><pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="4" stroke="{p["main"]}" stroke-opacity=".6" stroke-width="1"/></pattern></defs>')


def rect(x1, y1, x2, y2, cls="wall"):
    return f'<rect class="{cls}" x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}"/>'


def poly(points, cls="wall"):
    return f'<polygon class="{cls}" points="{" ".join(f"{x},{y}" for x, y in points)}"/>'


def label(x, y, name, dim=None, small=False):
    s = f'<text class="name{" sm" if small else ""}" x="{x}" y="{y}">{name.upper()}</text>'
    if dim:
        s += f'<text class="dim" x="{x}" y="{y + 11}">{dim}</text>'
    return s


def stairs(x1, y1, x2, y2, n=7, vertical=True):
    out = [rect(x1, y1, x2, y2, "wall")]
    for i in range(1, n):
        if vertical:
            x = x1 + (x2 - x1) * i / n
            out.append(f'<line class="stairs" x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y2}"/>')
        else:
            y = y1 + (y2 - y1) * i / n
            out.append(f'<line class="stairs" x1="{x1}" y1="{y:.1f}" x2="{x2}" y2="{y:.1f}"/>')
    return "".join(out)


def corner_ornaments(vb):
    x, y, w, h = vb
    L, o = 16, 4
    pts = []
    for cx, cy, sx, sy in ((x + o, y + o, 1, 1), (x + w - o, y + h - o, -1, -1)):
        pts.append(f'<path d="M{cx} {cy + sy * L} V{cy} H{cx + sx * L}" fill="none" stroke="{PAL["main"]}" stroke-width="2"/>')
        pts.append(f'<path d="M{cx + sx * 5} {cy + sy * (L - 5)} V{cy + sy * 5} H{cx + sx * (L - 5)}" fill="none" stroke="{PAL["main"]}" stroke-opacity=".5" stroke-width="1"/>')
    return "".join(pts)


def svg(vb, body, title, title_xy):
    x, y, w, h = vb
    tx, ty = title_xy
    t = (f'<text class="title" x="{tx}" y="{ty}">{title.upper()}</text>'
         f'<path class="orn" d="M{tx - 12} {ty - 5} l4 -4 4 4 -4 4z"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">'
            f"<style>{style_css(PAL)}</style>{defs_xml(PAL)}{body}{t}{corner_ornaments(vb)}</svg>")


# ---------------------------------------------------------------- MAIN FLOOR
MAIN_VB = (408, 150, 464, 636)
main_ext = [(533, 365), (790, 365), (790, 390), (858, 390), (858, 633), (793, 633), (793, 686),
            (721, 686), (721, 747), (533, 747)]
main = "".join([
    rect(533, 165, 643, 255, "out"), label(588, 212, "Deck", small=True),
    rect(533, 255, 740, 365, "out"), label(636, 296, "Patio", "BACKYARD"),
    rect(420, 178, 533, 343, "wall"), label(476, 262, "Garage", small=True),
    rect(533, 365, 640, 505), label(586, 432, "Bedroom", "13 × 12", small=True),
    rect(640, 365, 740, 460), label(690, 408, "Bath", small=True),
    rect(740, 365, 790, 390),
    rect(740, 390, 858, 505), label(799, 432, "Bedroom", "13 × 12", small=True),
    rect(533, 505, 672, 652), stairs(578, 505, 633, 532, 7, True), label(612, 590, "Kitchen", "10 × 10"),
    rect(672, 505, 858, 633), label(765, 566, "Living Room", "20 × 14"),
    rect(672, 560, 682, 608, "fire"),
    rect(533, 652, 601, 747), label(567, 704, "Nook", small=True),
    rect(601, 633, 721, 747), label(661, 684, "Dining", "12 × 12"),
    rect(721, 633, 793, 686), label(757, 664, "Entry", small=True),
    rect(721, 686, 793, 747, "out"), label(757, 722, "Porch", small=True),
    poly(main_ext, "ext"),
    rect(420, 178, 533, 343, "ext"),
])

# ---------------------------------------------------------------- UPPER FLOOR
UPPER_VB = (742, 72, 352, 306)
upper_ext = [(825, 95), (1015, 95), (1015, 120), (1080, 120), (1080, 188), (1015, 188), (1015, 210),
             (943, 210), (943, 365), (823, 365), (823, 230), (755, 230), (755, 150), (825, 150)]
upper = "".join([
    rect(825, 95, 898, 150), label(861, 127, "Bath", small=True),
    poly([(898, 95), (1015, 95), (1015, 120), (1080, 120), (1080, 188), (1015, 188), (1015, 210), (898, 210)]),
    label(975, 148, "Primary", small=False), label(975, 163, "Bedroom", "12 × 12"),
    rect(755, 150, 898, 230), stairs(755, 150, 835, 180, 8, True),
    rect(880, 210, 943, 275), label(911, 247, "Closet", small=True),
    poly([(823, 230), (880, 230), (880, 275), (943, 275), (943, 365), (823, 365)]),
    label(883, 305, "Imogen's", small=True), label(883, 319, "Office", "12 × 11"),
    poly(upper_ext, "ext"),
])

# ---------------------------------------------------------------- LOWER FLOOR
LOWER_VB = (746, 722, 350, 298)
lower = "".join([
    rect(758, 763, 1083, 1006),
    rect(758, 763, 948, 873), label(853, 812, "Laundry", "20 × 12"),
    rect(948, 763, 1083, 873), label(1015, 800, "Craft Room", "12 × 11", small=True),
    stairs(783, 873, 866, 900, 8, True),
    rect(758, 923, 820, 1006), label(789, 968, "Storage", small=True),
    rect(820, 947, 878, 1006), label(849, 980, "Bath", small=True),
    label(985, 930, "Library", "FAMILY ROOM · 20 × 13"),
    poly([(880, 990), (890, 1000), (904, 986), (894, 976)], "fire"),
    rect(758, 763, 1083, 1006, "ext"),
])

FLOORS = {
    "main": (MAIN_VB, main, "Main Floor", (572, 775)),
    "upper": (UPPER_VB, upper, "Upper Floor", (957, 330)),
    "lower": (LOWER_VB, lower, "Lower Floor", (772, 750)),
}

# ---------------------------------------------------------------- DEVICE MARKERS
# kind: lamp (toggle, glows), speaker, climate, sensor (status only), outdoor (light)
MARKERS = {
    "main": [
        ("switch.couch_lamp", "Couch", "mdi:lamp", 700, 530, "lamp"),
        ("switch.chez_lounge_lamp", "Chez Lounge", "mdi:lamp", 830, 530, "lamp"),
        ("switch.pappasan_lamp", "Pappasan", "mdi:floor-lamp", 830, 612, "lamp"),
        ("switch.lamp_window", "Window", "mdi:lamp", 765, 612, "lamp"),
        ("switch.grow_lamp", "Grow lamp", "mdi:sprout", 700, 612, "lamp"),
        ("media_player.billie_2", "Billie", "mdi:speaker", 765, 530, "speaker"),
        ("climate.nest_thermostat", "Thermostat", "mdi:thermostat", 690, 482, "climate"),
        ("media_player.kitchen_speaker", "Kitchen", "mdi:speaker", 560, 628, "speaker"),
        ("switch.dining_room_xmas", "Dining Xmas", "mdi:pine-tree", 661, 718, "lamp"),
        ("light.outdoor_dimmer_light_1", "Outdoor 1", "mdi:outdoor-lamp", 585, 345, "lamp"),
        ("light.outdoor_dimmer_light_2", "Outdoor 2", "mdi:outdoor-lamp", 690, 345, "lamp"),
    ],
    "upper": [
        ("sensor.hp_officejet_pro_6970", "Printer", "mdi:printer", 883, 345, "sensor"),
    ],
    "lower": [
        ("switch.torch_light_front", "Torch front", "mdi:torch", 925, 970, "lamp"),
        ("switch.torch_light_back", "Torch back", "mdi:torch", 1045, 970, "lamp"),
        ("switch.basement_fireplace_lights", "Fireplace", "mdi:fireplace", 925, 905, "lamp"),
        ("media_player.library", "Library", "mdi:speaker", 1045, 905, "speaker"),
        ("switch.painting_desk", "Painting desk", "mdi:palette", 985, 845, "lamp"),
        ("sensor.h2s_0938ac5b0600679_print_status", "Icarus", "mdi:printer-3d", 1050, 845, "sensor"),
        ("sensor.washer_current_status", "Washer", "mdi:washing-machine", 800, 848, "sensor"),
        ("sensor.dryer_current_status", "Dryer", "mdi:tumble-dryer", 905, 848, "sensor"),
    ],
}


# ---------------------------------------------------------------- LIGHT POOLS
# Each lamp lights only its own room: a warm radial glow clipped to the room shape.
LIVING = [(672, 505), (858, 505), (858, 633), (672, 633)]
DINING = [(601, 633), (721, 633), (721, 747), (601, 747)]
PATIO = [(533, 165), (643, 165), (643, 255), (740, 255), (740, 365), (533, 365)]
LIBRARY = [(758, 873), (1083, 873), (1083, 1006), (878, 1006), (878, 947), (820, 947), (820, 923), (758, 923)]
CRAFT = [(948, 763), (1083, 763), (1083, 873), (948, 873)]
GLOW_ROOMS = {
    "switch.couch_lamp": (LIVING, "255,196,120", 120),
    "switch.chez_lounge_lamp": (LIVING, "255,196,120", 120),
    "switch.pappasan_lamp": (LIVING, "255,190,110", 130),
    "switch.lamp_window": (LIVING, "255,200,130", 110),
    "switch.grow_lamp": (LIVING, "214,110,255", 95),
    "switch.dining_room_xmas": (DINING, "255,170,90", 110),
    "light.outdoor_dimmer_light_1": (PATIO, "255,205,140", 150),
    "light.outdoor_dimmer_light_2": (PATIO, "255,205,140", 150),
    "switch.torch_light_front": (LIBRARY, "255,170,80", 140),
    "switch.torch_light_back": (LIBRARY, "255,170,80", 140),
    "switch.basement_fireplace_lights": (LIBRARY, "255,140,60", 150),
    "switch.painting_desk": (CRAFT, "255,214,160", 110),
}


def glow_svg(vb, room, rgb, radius, x, y):
    vx, vy, vw, vh = vb
    pts = " ".join(f"{a},{b}" for a, b in room)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}">'
            f'<defs><clipPath id="c"><polygon points="{pts}"/></clipPath>'
            f'<radialGradient id="g" cx="{x}" cy="{y}" r="{radius}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="rgb({rgb})" stop-opacity=".62"/>'
            f'<stop offset=".45" stop-color="rgb({rgb})" stop-opacity=".26"/>'
            f'<stop offset="1" stop-color="rgb({rgb})" stop-opacity="0"/></radialGradient></defs>'
            f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#g)" clip-path="url(#c)"/></svg>')


def pct(vb, x, y):
    vx, vy, vw, vh = vb
    return round((x - vx) / vw * 100, 2), round((y - vy) / vh * 100, 2)


def main_():
    global PAL
    OUT.mkdir(parents=True, exist_ok=True)
    markers = {}
    for name, pal in PALETTES.items():
        PAL = pal
        for key, (vb, body, title, txy) in FLOORS.items():
            p = OUT / f"floor_{key}{pal['suffix']}.svg"
            p.write_text(svg(vb, body, title, txy), encoding="utf-8")
            print(p.name, p.stat().st_size, "bytes")
            if name != "gold":
                continue
            markers[key] = []
            for e, n, i, x, y, k in MARKERS.get(key, []):
                m = {"entity": e, "name": n, "icon": i, "kind": k, "left": pct(vb, x, y)[0], "top": pct(vb, x, y)[1]}
                if e in GLOW_ROOMS:
                    m["glow"] = "glow_" + e.replace(".", "_") + ".svg"
                markers[key].append(m)
            markers[key + "_aspect"] = round(vb[2] / vb[3], 4)
        for key, (vb, body, title, txy) in FLOORS.items():
            for e, n, i, x, y, k in MARKERS.get(key, []):
                if e in GLOW_ROOMS:
                    room, rgb, r = GLOW_ROOMS[e]
                    fn = pal["glow_prefix"] + e.replace(".", "_") + ".svg"
                    (OUT / fn).write_text(glow_svg(vb, room, pal["glow_rgb"] or rgb, r, x, y), encoding="utf-8")
    (ROOT / "tools" / "floor_markers.json").write_text(json.dumps(markers, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main_()
