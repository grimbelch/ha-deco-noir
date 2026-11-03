"""Generate a starter Sweet Home 3D model (house.sh3d) from the measured floor plan.

Three levels (Lower / Main / Upper), exterior + interior walls, named rooms, and one
light per Home Assistant lamp, *named with its entity id* so the
shmuelzon/home-assistant-floor-plan plugin can render one layer per light.

Coordinates come from the same pixel space as make_floorplan.py. Scale: the lower floor
is 35.8 ft x 26.8 ft = 325 x 243 px  ->  9.08 px/ft  ->  3.357 cm/px.
Floor alignment (estimated from matching widths; adjust in Sweet Home 3D if needed):
  main  : origin at its NW corner (533, 365)
  lower : sits under the main floor's bedroom/living band (lower y 763 == main y 390)
  upper : left edges aligned, top at the main floor's top wall (upper y 95 == main y 365)

Output: build/house.sh3d (a zip with Home.xml + a small bulb model).
"""
import math, pathlib, struct, zipfile, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "house.sh3d"
S = 30.48 / 9.08  # cm per px

FLOOR_H, SLAB = 250.0, 12.0
LEVELS = [("lvl_lower", "Lower Floor", 0.0, 0), ("lvl_main", "Main Floor", FLOOR_H + SLAB, 1),
          ("lvl_upper", "Upper Floor", 2 * (FLOOR_H + SLAB), 2)]

# floor -> (px offset to main-floor space)
OFF = {"lvl_main": (0, 0), "lvl_lower": (533 - 758, 390 - 763), "lvl_upper": (533 - 755, 365 - 95)}
ORIGIN = (533, 365)


def to_cm(level, x, y):
    dx, dy = OFF[level]
    return round((x + dx - ORIGIN[0]) * S, 1), round((y + dy - ORIGIN[1]) * S, 1)


def R(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


# ---------------------------------------------------------------- rooms (name, polygon, walled?)
ROOMS = {
    "lvl_main": [
        ("Bedroom (west)", R(533, 365, 640, 505), True),
        ("Bath", R(640, 365, 740, 460), True),
        ("Closet", R(740, 365, 790, 390), True),
        ("Bedroom (east)", R(740, 390, 858, 505), True),
        ("Hall", R(640, 460, 740, 505), True),
        ("Kitchen", R(533, 505, 672, 652), True),
        ("Living Room", R(672, 505, 858, 633), True),
        ("Nook", R(533, 652, 601, 747), True),
        ("Dining", R(601, 633, 721, 747), True),
        ("Entry", R(721, 633, 793, 686), True),
        ("Garage", R(420, 178, 533, 343), True),
        ("Porch", R(721, 686, 793, 747), False),
        ("Deck", R(533, 165, 643, 255), False),
        ("Patio", R(533, 255, 740, 365), False),
    ],
    "lvl_upper": [
        ("Bath", R(825, 95, 898, 150), True),
        ("Primary Bedroom", [(898, 95), (1015, 95), (1015, 120), (1080, 120), (1080, 188), (1015, 188), (1015, 210), (898, 210)], True),
        ("Landing", R(755, 150, 898, 230), True),
        ("Closet", R(880, 210, 943, 275), True),
        ("Imogen's Office", [(823, 230), (880, 230), (880, 275), (943, 275), (943, 365), (823, 365)], True),
    ],
    "lvl_lower": [
        ("Laundry", R(758, 763, 948, 873), True),
        ("Craft Room", R(948, 763, 1083, 873), True),
        ("Library", [(758, 873), (1083, 873), (1083, 1006), (878, 1006), (878, 947), (820, 947), (820, 923), (758, 923)], True),
        ("Storage", R(758, 923, 820, 1006), True),
        ("Bath", R(820, 947, 878, 1006), True),
    ],
}

EXTERIOR = {
    "lvl_main": [[(533, 365), (790, 365), (790, 390), (858, 390), (858, 633), (793, 633), (793, 686),
                  (721, 686), (721, 747), (533, 747)], R(420, 178, 533, 343)],
    "lvl_upper": [[(825, 95), (1015, 95), (1015, 120), (1080, 120), (1080, 188), (1015, 188), (1015, 210),
                   (943, 210), (943, 365), (823, 365), (823, 230), (755, 230), (755, 150), (825, 150)]],
    "lvl_lower": [R(758, 763, 1083, 1006)],
}

# ---------------------------------------------------------------- lamps (entity id, level, px x, px y, elevation cm)
LIGHTS = [
    ("switch.couch_lamp", "lvl_main", 700, 530, 110),
    ("switch.chez_lounge_lamp", "lvl_main", 830, 530, 110),
    ("switch.pappasan_lamp", "lvl_main", 830, 612, 150),
    ("switch.lamp_window", "lvl_main", 765, 612, 110),
    ("switch.grow_lamp", "lvl_main", 700, 612, 90),
    ("switch.dining_room_xmas", "lvl_main", 661, 718, 160),
    ("light.outdoor_dimmer_light_1", "lvl_main", 585, 345, 220),
    ("light.outdoor_dimmer_light_2", "lvl_main", 690, 345, 220),
    ("switch.torch_light_front", "lvl_lower", 925, 970, 150),
    ("switch.torch_light_back", "lvl_lower", 1045, 970, 150),
    ("switch.basement_fireplace_lights", "lvl_lower", 925, 905, 100),
    ("switch.painting_desk", "lvl_lower", 985, 845, 110),
]
LIGHT_COLOR = {"switch.grow_lamp": "D66EFF", "switch.basement_fireplace_lights": "FF8C3C"}


# ---------------------------------------------------------------- wall builder
def edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def axis_intervals(segs):
    """Group axis-aligned segments by line and merge overlapping intervals."""
    lines = {}
    for (x1, y1), (x2, y2) in segs:
        if y1 == y2:
            key, a, b = ("h", y1), min(x1, x2), max(x1, x2)
        elif x1 == x2:
            key, a, b = ("v", x1), min(y1, y2), max(y1, y2)
        else:
            continue
        lines.setdefault(key, []).append([a, b])
    out = {}
    for k, iv in lines.items():
        iv.sort()
        merged = [iv[0][:]]
        for a, b in iv[1:]:
            if a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        out[k] = merged
    return out


def subtract(iv, cut):
    res = []
    for a, b in iv:
        parts = [[a, b]]
        for c, d in cut:
            nxt = []
            for p, q in parts:
                if d <= p or c >= q:
                    nxt.append([p, q])
                else:
                    if c > p:
                        nxt.append([p, c])
                    if d < q:
                        nxt.append([d, q])
            parts = nxt
        res += [p for p in parts if p[1] - p[0] > 2]
    return res


def walls_for(level):
    ext_segs = [e for poly in EXTERIOR[level] for e in edges(poly)]
    int_segs = [e for name, poly, walled in ROOMS[level] if walled for e in edges(poly)]
    ext = axis_intervals(ext_segs)
    inn = axis_intervals(int_segs)
    walls = []
    for (k, v), ivs in ext.items():
        for a, b in ivs:
            walls.append(((a, v, b, v) if k == "h" else (v, a, v, b), 20.0))
    for (k, v), ivs in inn.items():
        for a, b in subtract(ivs, ext.get((k, v), [])):
            walls.append(((a, v, b, v) if k == "h" else (v, a, v, b), 10.0))
    return walls


# ---------------------------------------------------------------- tiny bulb model (OBJ sphere) + icon
def sphere_obj(n=10):
    v, f = [], []
    for i in range(n + 1):
        t = math.pi * i / n
        for j in range(n):
            p = 2 * math.pi * j / n
            v.append((0.5 * math.sin(t) * math.cos(p), 0.5 * math.cos(t), 0.5 * math.sin(t) * math.sin(p)))
    for i in range(n):
        for j in range(n):
            a, b = i * n + j + 1, i * n + (j + 1) % n + 1
            c, d = (i + 1) * n + (j + 1) % n + 1, (i + 1) * n + j + 1
            f.append((a, b, c, d))
    return "mtllib bulb.mtl\nusemtl bulb\n" + "".join(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in v) + \
        "".join(f"f {a} {b} {c} {d}\n" for a, b, c, d in f)


MTL = "newmtl bulb\nKa 1 0.92 0.75\nKd 1 0.92 0.75\nKs 0 0 0\nd 0.85\n"


def png_icon():
    raw = b"".join(b"\x00" + bytes([230, 207, 154, 255]) * 8 for _ in range(8))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 6, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


# ---------------------------------------------------------------- Home.xml
def esc(s):
    return s.replace("&", "&amp;").replace("'", "&apos;").replace("<", "&lt;")


def home_xml():
    L = ["<?xml version='1.0'?>",
         "<home version='7500' name='house.sh3d' camera='topCamera' selectedLevel='lvl_main' wallHeight='250.0'>",
         "  <property name='com.eteks.sweethome3d.SweetHome3D.ExpandedGroups' value=''/>",
         "  <environment groundColor='FF2A2824' skyColor='FF11131C' lightColor='FF555555' wallsAlpha='0.0'/>",
         "  <observerCamera attribute='observerCamera' lens='PINHOLE' x='600.0' y='900.0' z='170.0' yaw='3.1415927' pitch='0.2' fieldOfView='1.0995574' time='1793700000000'/>",
         # aerial view from the south, looking north and down (good starting point for the plugin)
         "  <camera attribute='topCamera' lens='PINHOLE' x='545.0' y='2400.0' z='2300.0' yaw='0.0' pitch='0.85' fieldOfView='0.7853982' time='1793700000000'/>"]
    for lid, name, elev, idx in LEVELS:
        L.append(f"  <level id='{lid}' name='{esc(name)}' elevation='{elev}' floorThickness='{SLAB}' height='{FLOOR_H}' elevationIndex='{idx}' viewable='true'/>")
    n = 0
    for lid, _, _, _ in LEVELS:
        for (x1, y1, x2, y2), th in walls_for(lid):
            a, b = to_cm(lid, x1, y1), to_cm(lid, x2, y2)
            n += 1
            L.append(f"  <wall id='wall{n}' level='{lid}' xStart='{a[0]}' yStart='{a[1]}' xEnd='{b[0]}' yEnd='{b[1]}' height='{FLOOR_H}' thickness='{th}' pattern='hatchUp'/>")
    r = 0
    for lid, rooms in ROOMS.items():
        for name, poly, walled in rooms:
            r += 1
            ceiling = "true" if walled else "false"
            L.append(f"  <room id='room{r}' level='{lid}' name='{esc(name)}' areaVisible='true' ceilingVisible='{ceiling}' floorVisible='true'>")
            for x, y in poly:
                cx, cy = to_cm(lid, x, y)
                L.append(f"    <point x='{cx}' y='{cy}'/>")
            L.append("  </room>")
    for i, (ent, lid, x, y, elev) in enumerate(LIGHTS, 1):
        cx, cy = to_cm(lid, x, y)
        col = LIGHT_COLOR.get(ent, "FFD9A0")
        L.append(f"  <light id='light{i}' level='{lid}' name='{ent}' model='bulb.obj' icon='bulb.png' "
                 f"x='{cx}' y='{cy}' elevation='{elev}' width='14.0' depth='14.0' height='14.0' power='0.5' "
                 f"movable='true' doorOrWindow='false'>")
        L.append(f"    <lightSource x='0.5' y='0.5' z='0.5' color='FF{col}' diameter='0.6'/>")
        L.append("  </light>")
    L.append("</home>")
    return "\n".join(L), n, r


def main():
    xml, nw, nr = home_xml()
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Home.xml", xml)
        z.writestr("bulb.obj", sphere_obj())
        z.writestr("bulb.mtl", MTL)
        z.writestr("bulb.png", png_icon())
    print(f"{OUT}  walls={nw} rooms={nr} lights={len(LIGHTS)}  {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
