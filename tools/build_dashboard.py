"""Build and push the Deco Noir 'home-hub' dashboard (Phase 2).

Usage:  HA_URL=ws://192.168.0.200/api/websocket HA_TOKEN_FILE=<path> python tools/build_dashboard.py [--dry-run]

- Home view: rebuilt from Deco templates (lobby, scenes, room banners, deco tiles, gauges).
- Floor Plan view: picture-elements over www/deco/floor_*.svg with deco_marker buttons.
- Media / Yard / Alexandria: existing cards kept; heading cards become Deco marquees.
"""
import json, os, pathlib, sys
import websocket

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from deco_templates import TEMPLATES, ART  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = os.environ.get("HA_URL", "ws://192.168.0.200/api/websocket")
TOKEN = pathlib.Path(os.environ["HA_TOKEN_FILE"]).read_text().strip()
DASH = "home-hub"
THEME = "deco_noir"
ASSET_V = "3"  # bump to bust caches when SVGs change
P = "h2s_0938ac5b0600679"

ws = websocket.create_connection(URL, timeout=60)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"
_n = [0]


def call(m):
    _n[0] += 1
    m["id"] = _n[0]
    ws.send(json.dumps(m))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == _n[0]:
            return r


# ---------------------------------------------------------------- helpers
def marquee(title):
    return {"type": "custom:button-card", "template": "deco_marquee", "variables": {"title": title},
            "grid_options": {"columns": "full"}}


def tile(entity, name, icon, cols=6, action=None):
    c = {"type": "custom:button-card", "template": "deco_tile", "entity": entity, "name": name, "icon": icon,
         "grid_options": {"columns": cols, "rows": 2}}
    if action:
        c["tap_action"] = {"action": action}
    return c


def scene(name, icon, action, target, data=None):
    act = {"action": "perform-action", "perform_action": action, "target": target}
    if data:
        act["data"] = data
    return {"type": "custom:button-card", "template": "deco_scene", "name": name, "icon": icon,
            "tap_action": act, "grid_options": {"columns": 6, "rows": 2}}


def room(name, art, lamps, accent, line2=None):
    v = {"lamps": lamps, "art_svg": ART[art]}
    if line2:
        v.update({"line2_entity": line2[0], "line2_label": line2[1]})
        if len(line2) > 2:
            v["line2_attr"] = line2[2]
        if len(line2) > 3:
            v["line2_unit"] = line2[3]
    return {"type": "custom:button-card", "template": "deco_room", "name": name, "variables": v,
            "styles": {"card": [f"--room-accent: {accent}"]},
            "grid_options": {"columns": "full", "rows": 2}}


def section(*cards, span=1):
    s = {"type": "grid", "cards": list(cards)}
    if span > 1:
        s["column_span"] = span
    return s


LAMPS_ALL = ["switch.chez_lounge_lamp", "switch.couch_lamp", "switch.pappasan_lamp", "switch.grow_lamp",
             "switch.lamp_window", "switch.torch_light_front", "switch.torch_light_back",
             "switch.basement_fireplace_lights", "switch.painting_desk", "switch.dining_room_xmas"]
SPEAKERS = ["media_player.billie_2", "media_player.library", "media_player.kitchen_speaker", "media_player.spotify"]

# ---------------------------------------------------------------- HOME
home = {
    "type": "sections", "title": "Home", "path": "home", "icon": "mdi:home-heart", "max_columns": 4, "theme": THEME,
    "sections": [
        section({"type": "custom:button-card", "template": "deco_lobby", "grid_options": {"columns": "full"}}, span=4),

        section(marquee("Scenes"),
                scene("Living room on", "mdi:sofa-outline", "switch.turn_on",
                      {"entity_id": ["switch.chez_lounge_lamp", "switch.couch_lamp", "switch.pappasan_lamp"]}),
                scene("Good night", "mdi:weather-night", "script.turn_on", {"entity_id": "script.good_night"}),
                scene("All lamps off", "mdi:lightbulb-group-off-outline", "switch.turn_off", {"entity_id": LAMPS_ALL}),
                scene("Pause music", "mdi:pause-circle-outline", "media_player.media_pause", {"entity_id": SPEAKERS}),
                span=2),

        section(marquee("Climate"),
                {"type": "thermostat", "entity": "climate.nest_thermostat", "name": "Thermostat",
                 "features": [{"type": "climate-hvac-modes", "hvac_modes": ["off", "heat", "cool", "heat_cool"]}],
                 "grid_options": {"columns": "full"}},
                span=2),

        section(room("Living Room", "living",
                     ["switch.couch_lamp", "switch.chez_lounge_lamp", "switch.pappasan_lamp", "switch.lamp_window", "switch.grow_lamp"],
                     "var(--deco-gold)", ("media_player.billie_2", "Billie")),
                tile("switch.couch_lamp", "Couch", "mdi:lamp-outline", 4),
                tile("switch.chez_lounge_lamp", "Chez Lounge", "mdi:lamp-outline", 4),
                tile("switch.pappasan_lamp", "Pappasan", "mdi:floor-lamp-outline", 4),
                tile("switch.lamp_window", "Window", "mdi:lamp-outline", 4),
                tile("switch.grow_lamp", "Grow lamp", "mdi:sprout-outline", 4),
                tile("media_player.billie_2", "Billie", "mdi:speaker", 4, "more-info"),
                span=2),

        section(room("Library", "library",
                     ["switch.torch_light_front", "switch.torch_light_back", "switch.basement_fireplace_lights"],
                     "var(--deco-sapphire)", ("media_player.library", "Speaker")),
                tile("switch.torch_light_front", "Torch front", "mdi:torch"),
                tile("switch.torch_light_back", "Torch back", "mdi:torch"),
                tile("switch.basement_fireplace_lights", "Fireplace", "mdi:fireplace"),
                tile("media_player.library", "Speaker", "mdi:speaker", 6, "more-info")),

        section(room("Outside", "outside", ["light.outdoor_dimmer_light_1", "light.outdoor_dimmer_light_2"],
                     "var(--deco-emerald)", ("binary_sensor.rachio_9207aa_rain", "Rain sensor")),
                tile("light.outdoor_dimmer_light_1", "Outdoor 1", "mdi:outdoor-lamp"),
                tile("light.outdoor_dimmer_light_2", "Outdoor 2", "mdi:outdoor-lamp"),
                tile("automation.outdoor_lights_sunset_to_10_pm", "Sunset schedule", "mdi:weather-sunset"),
                tile("switch.rachio_9207aa_rain_delay", "Rain delay", "mdi:weather-pouring")),

        section(room("Around the House", "house",
                     ["switch.dining_room_xmas", "switch.painting_desk"], "var(--deco-gold)",
                     ("sensor.hp_officejet_pro_6970", "Printer")),
                tile("switch.dining_room_xmas", "Dining Xmas", "mdi:pine-tree"),
                tile("switch.painting_desk", "Painting desk", "mdi:palette-outline"),
                tile("media_player.kitchen_speaker", "Kitchen", "mdi:speaker", 6, "more-info"),
                tile("sensor.hp_officejet_pro_6970", "Printer", "mdi:printer-outline", 6, "more-info")),

        section(room("Workshop", "workshop", [], "var(--deco-garnet)",
                     (f"sensor.{P}_print_progress", "Icarus", None, "%")),
                {"type": "picture-entity", "entity": f"camera.{P}_camera", "camera_view": "auto",
                 "show_name": False, "show_state": False, "grid_options": {"columns": 12}},
                {"type": "custom:button-card", "template": "deco_rows", "entity": f"sensor.{P}_print_status",
                 "name": "Icarus · H2S", "icon": "mdi:printer-3d",
                 "variables": {"rows": [
                     {"label": "Job", "entity": f"sensor.{P}_task_name"},
                     {"label": "Progress", "entity": f"sensor.{P}_print_progress", "unit": "%"},
                     {"label": "Time left", "entity": f"sensor.{P}_remaining_time", "unit": " h"},
                     {"label": "Nozzle", "entity": f"sensor.{P}_nozzle_temperature", "unit": "°", "round": 0},
                     {"label": "Bed", "entity": f"sensor.{P}_bed_temperature", "unit": "°", "round": 0},
                     {"label": "AMS humidity", "entity": f"sensor.{P}_ams_1_humidity", "unit": "%"}]},
                 "grid_options": {"columns": 12}},
                span=2),

        section(marquee("Now Playing"),
                {"type": "media-control", "entity": "media_player.spotify", "name": "Spotify", "grid_options": {"columns": "full"}},
                span=2),

        section(marquee("Alexandria"),
                {"type": "custom:button-card", "template": "deco_gauge", "entity": "sensor.alexandria_battery",
                 "name": "UPS battery", "grid_options": {"columns": 6, "rows": 3}},
                {"type": "custom:button-card", "template": "deco_gauge", "entity": "sensor.alexandria_load",
                 "name": "UPS load", "grid_options": {"columns": 6, "rows": 3}},
                {"type": "custom:button-card", "template": "deco_rows", "entity": "sensor.alexandria_status",
                 "name": "Server", "icon": "mdi:server",
                 "styles": {"custom_fields": {"badge": ["display: none"]}},
                 "variables": {"rows": [
                     {"label": "Runtime on battery", "entity": "sensor.alexandria_time_left", "unit": " min", "round": 0},
                     {"label": "Mains voltage", "entity": "sensor.alexandria_input_voltage", "unit": " V", "round": 0},
                     {"label": "Array free", "entity": "sensor.sabnzbd_free_disk_space", "unit": " GB", "round": 0},
                     {"label": "Ads blocked today", "entity": "sensor.pi_hole_ads_blocked"}]},
                 "grid_options": {"columns": "full"}},
                span=2),
    ],
}

# ---------------------------------------------------------------- FLOOR PLAN
markers = json.loads((ROOT / "tools" / "floor_markers.json").read_text())


def marker(m):
    c = {"type": "custom:button-card", "template": "deco_marker", "entity": m["entity"], "name": m["name"],
         "icon": m["icon"], "style": {"left": f'{m["left"]}%', "top": f'{m["top"]}%'}}
    if m["kind"] in ("speaker", "climate", "sensor"):
        c["tap_action"] = {"action": "more-info"}
    if m["kind"] == "climate":
        c["name"] = "[[[ const a=entity.attributes; return Math.round(a.current_temperature)+'° · set '+Math.round(a.temperature||0)+'°'; ]]]"
    if m["kind"] == "sensor":
        c["name"] = "[[[ return '" + m["name"] + " · ' + helpers.localize(entity); ]]]"
    return c


def plan(key):
    return {"type": "picture-elements", "image": f"/local/deco/floor_{key}.svg?v={ASSET_V}",
            "elements": [marker(m) for m in markers[key]], "grid_options": {"columns": "full"}}


floor = {
    "type": "sections", "title": "Floor Plan", "path": "floor-plan", "icon": "mdi:floor-plan", "max_columns": 2,
    "theme": THEME,
    "sections": [
        section(marquee("Main Floor"), plan("main"), span=2),
        section(marquee("Upper Floor"), plan("upper")),
        section(marquee("Lower Floor"), plan("lower")),
    ],
}


# ---------------------------------------------------------------- other views: headings -> marquees
def decorate(view):
    view = json.loads(json.dumps(view))
    view["theme"] = THEME
    for s in view.get("sections", []):
        s["cards"] = [marquee(c.get("heading", "")) if c.get("type") == "heading" else c for c in s.get("cards", [])]
    view.pop("badges", None) if view.get("path") == "home" else None
    return view


def main():
    dry = "--dry-run" in sys.argv
    cur = call({"type": "lovelace/config", "url_path": DASH})["result"]
    out_dir = ROOT / "dashboards"
    out_dir.mkdir(exist_ok=True)
    if not (out_dir / "home-hub.before-phase2.json").exists():
        (out_dir / "home-hub.before-phase2.json").write_text(json.dumps(cur, indent=2), encoding="utf-8")
    keep = [decorate(v) for v in cur["views"] if v.get("path") in ("media", "yard", "alexandria")]
    cfg = {"title": cur.get("title", "Home"), "button_card_templates": TEMPLATES, "views": [home, floor] + keep}
    (ROOT / "templates").mkdir(exist_ok=True)
    (ROOT / "templates" / "deco_templates.json").write_text(json.dumps(TEMPLATES, indent=2), encoding="utf-8")
    (out_dir / "home-hub.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    if dry:
        print("dry run: wrote dashboards/home-hub.json")
        return
    r = call({"type": "lovelace/config/save", "url_path": DASH, "config": cfg})
    print("save:", r.get("success"), r.get("error"))
    print("views:", [v["title"] for v in cfg["views"]])
    states = {s["entity_id"] for s in call({"type": "get_states"})["result"]}
    refs = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "entity" and isinstance(v, str) and "." in v:
                    refs.add(v)
                elif k == "entity_id" and isinstance(v, (str, list)):
                    refs.update([v] if isinstance(v, str) else v)
                elif k in ("lamps", "triggers_update") and isinstance(v, list):
                    refs.update(x for x in v if "." in x)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(cfg["views"])
    walk(TEMPLATES)
    print("missing entities:", sorted(x for x in refs if x not in states))


if __name__ == "__main__":
    main()
