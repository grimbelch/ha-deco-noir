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
from seasons_dashboard import apply_seasons
from cogitator_dashboard import apply_cogitator

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = os.environ.get("HA_URL", "ws://192.168.0.200/api/websocket")
TOKEN = pathlib.Path(os.environ["HA_TOKEN_FILE"]).read_text().strip()
DASH = "home-hub"
THEME = None  # theme comes from the HA default (toggled via input_select.dashboard_theme)
ASSET_V = "4"  # bump to bust caches when SVGs change
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


# ---------------------------------------------------------------- button-card style normalisation
# Templates are written with readable "prop: value" strings; button-card needs [{prop: value}] and
# grid-template-areas without the YAML-style outer single quotes.
def _style_item(item):
    if not isinstance(item, str) or ":" not in item:
        return item
    prop, val = item.split(":", 1)
    val = val.strip()
    if prop.strip() == "grid-template-areas" and len(val) > 1 and val[0] == "'" and val[-1] == "'":
        val = val[1:-1]
    return {prop.strip(): val}


def normalize_styles(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k == "styles" and isinstance(v, dict):
                out[k] = {sk: ({fk: [_style_item(i) for i in fv] for fk, fv in sv.items()} if sk == "custom_fields" and isinstance(sv, dict)
                               else [_style_item(i) for i in sv] if isinstance(sv, list) else normalize_styles(sv))
                          for sk, sv in v.items()}
            else:
                out[k] = normalize_styles(v)
        return out
    if isinstance(o, list):
        return [normalize_styles(x) for x in o]
    return o


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
# Home = what you use every day: scenes, music, climate, then rooms in floor order (main -> lower -> outside),
# then appliances. Printers/servers/downloads live on their own tabs (Workshop, Alexandria, Media).
BAMBU_PRINTER = "ffee4738686992f668bd921495f6fb9a"   # device ids from the HA device registry
BAMBU_AMS = "3938769c64fa7bcb59d95b6dc46b6862"
home = {
    "type": "sections", "title": "Home", "path": "home", "icon": "mdi:home-heart", "max_columns": 4,
    "sections": [
        section({"type": "custom:button-card", "template": "deco_lobby", "grid_options": {"columns": "full"}}, span=4),

        section(marquee("Scenes"),
                scene("Living room on", "mdi:sofa-outline", "switch.turn_on",
                      {"entity_id": ["switch.chez_lounge_lamp", "switch.couch_lamp", "switch.pappasan_lamp"]}),
                scene("Good night", "mdi:weather-night", "script.turn_on", {"entity_id": "script.good_night"}),
                scene("All lamps off", "mdi:lightbulb-group-off-outline", "switch.turn_off", {"entity_id": LAMPS_ALL}),
                scene("Pause music", "mdi:pause-circle-outline", "media_player.media_pause", {"entity_id": SPEAKERS}),
                {"type": "custom:button-card", "template": "deco_theme_toggle", "entity": "input_select.dashboard_theme",
                 "grid_options": {"columns": "full", "rows": 1}},
                marquee("Now Playing"),
                {"type": "media-control", "entity": "media_player.spotify", "name": "Spotify", "grid_options": {"columns": "full"}},
                span=2),

        section(marquee("Climate"),
                {"type": "thermostat", "entity": "climate.nest_thermostat", "name": "Thermostat",
                 "features": [{"type": "climate-hvac-modes", "hvac_modes": ["off", "heat", "cool", "heat_cool"]}],
                 "grid_options": {"columns": "full"}},
                span=1),

        # Main floor
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

        section(room("Kitchen", "house", ["switch.dining_room_xmas"], "var(--deco-gold)",
                     ("media_player.kitchen_speaker", "Kitchen speaker")),
                tile("switch.dining_room_xmas", "Dining Xmas", "mdi:pine-tree"),
                tile("media_player.kitchen_speaker", "Kitchen speaker", "mdi:speaker", 6, "more-info")),

        # Lower floor
        section(room("Library", "library",
                     ["switch.torch_light_front", "switch.torch_light_back", "switch.basement_fireplace_lights"],
                     "var(--deco-sapphire)", ("media_player.library", "Speaker")),
                tile("switch.torch_light_front", "Torch front", "mdi:torch"),
                tile("switch.torch_light_back", "Torch back", "mdi:torch"),
                tile("switch.basement_fireplace_lights", "Fireplace", "mdi:fireplace"),
                tile("media_player.library", "Speaker", "mdi:speaker", 6, "more-info")),

        section(room("Craft Room", "workshop", ["switch.painting_desk"], "var(--deco-garnet)",
                     (f"sensor.{P}_print_status", "Icarus")),
                tile("switch.painting_desk", "Painting desk", "mdi:palette-outline"),
                tile(f"sensor.{P}_print_status", "Icarus", "mdi:printer-3d", 6, "more-info")),

        # Outdoors
        section(room("Outside", "outside", ["light.outdoor_dimmer_light_1", "light.outdoor_dimmer_light_2"],
                     "var(--deco-emerald)", ("binary_sensor.rachio_9207aa_rain", "Rain sensor")),
                tile("light.outdoor_dimmer_light_1", "Outdoor 1", "mdi:outdoor-lamp"),
                tile("light.outdoor_dimmer_light_2", "Outdoor 2", "mdi:outdoor-lamp"),
                tile("automation.outdoor_lights_sunset_to_10_pm", "Sunset schedule", "mdi:weather-sunset"),
                tile("switch.rachio_9207aa_rain_delay", "Rain delay", "mdi:weather-pouring")),

        section(room("Laundry", "house", [], "var(--deco-gold)",
                     ("sensor.washer_current_status", "Washer")),
                tile("sensor.washer_current_status", "Washer", "mdi:washing-machine", 6, "more-info"),
                tile("sensor.dryer_current_status", "Dryer", "mdi:tumble-dryer", 6, "more-info"),
                tile("fan.air_purifier_fan", "Air purifier", "mdi:air-purifier"),
                tile("sensor.hp_officejet_pro_6970", "Inkjet printer", "mdi:printer-outline", 6, "more-info")),
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
        c["name"] = "[[[ const a=entity.attributes; return Math.round(a.current_temperature)+'° / '+Math.round(a.temperature||0)+'°'; ]]]"
    if m["kind"] == "sensor":
        c["name"] = "[[[ return '" + m["name"] + " · ' + helpers.localize(entity); ]]]"
    return c


def glow(m):
    return {"type": "custom:button-card", "template": "deco_glow", "entity": m["entity"],
            "variables": {"img": f"/local/deco/{m['glow']}?v={ASSET_V}"},
            # button-card sets max-width: fit-content on itself; min-width wins, so the layer spans the plan
            "style": {"left": "0", "top": "0", "transform": "none", "width": "100%", "height": "100%",
                      "min-width": "100%", "display": "block", "pointer-events": "none", "mix-blend-mode": "screen"}}


def plan(key):
    pools = [glow(m) for m in markers[key] if m.get("glow")]
    return {"type": "picture-elements", "image": f"/local/deco/floor_{key}.svg?v={ASSET_V}",
            "elements": pools + [marker(m) for m in markers[key]], "grid_options": {"columns": "full"}}


floor = {
    "type": "sections", "title": "Floor Plan", "path": "floor-plan", "icon": "mdi:floor-plan", "max_columns": 3,
    "sections": [
        section(marquee("Main Floor"), plan("main"), span=2),
        section(marquee("Upper Floor"), plan("upper"), marquee("Lower Floor"), plan("lower")),
    ],
}



# ---------------------------------------------------------------- MEDIA / YARD / WORKSHOP / ALEXANDRIA
def dtile(entity, name, icon, cols=6, action="more-info"):
    return tile(entity, name, icon, cols, action)


def native_tile(entity, name, icon, feature):
    return {"type": "tile", "entity": entity, "name": name, "icon": icon,
            "features": [{"type": feature}], "features_position": "bottom"}


NOW_PLAYING_MD = ("{% set j = states.media_player | selectattr('attributes.media_title','defined') | "
                  "selectattr('state','in',['playing','paused']) | list %}{% if j %}{% for m in j %}"
                  "**{{ m.name }}**: {{ m.attributes.media_title }}{% if m.attributes.media_series_title %} "
                  "({{ m.attributes.media_series_title }}){% endif %}\n\n{% endfor %}"
                  "{% else %}_Nothing playing right now._{% endif %}")

media = {
    "type": "sections", "title": "Media", "path": "media", "icon": "mdi:play-box-multiple", "max_columns": 4,
    "sections": [
        section(marquee("Spotify"),
                {"type": "media-control", "entity": "media_player.spotify", "name": "Spotify"},
                {"type": "tile", "entity": "media_player.spotify", "name": "Volume", "icon": "mdi:volume-high",
                 "hide_state": True, "features": [{"type": "media-player-volume-slider"}], "features_position": "bottom"},
                {"type": "tile", "entity": "media_player.spotify", "name": "Playing on", "icon": "mdi:cast-audio",
                 "state_content": "source", "tap_action": {"action": "more-info"}}, span=2),
        section(marquee("Speakers"),
                {"type": "media-control", "entity": "media_player.billie_2", "name": "Billie"},
                {"type": "media-control", "entity": "media_player.library", "name": "Library"},
                native_tile("media_player.kitchen_speaker", "Kitchen speaker", "mdi:speaker", "media-player-volume-slider"),
                native_tile("media_player.all_speakers", "All speakers (group)", "mdi:speaker-multiple", "media-player-volume-slider"),
                span=2),
        section(marquee("Jellyfin"),
                dtile("sensor.alexandria_jellyfin_active_clients", "Jellyfin viewers", "mdi:account-multiple"),
                {"type": "markdown", "content": NOW_PLAYING_MD}),
        section(marquee("Downloads"),
                dtile("sensor.sabnzbd_status", "SABnzbd", "mdi:download"),
                dtile("sensor.sabnzbd_speed", "Speed", "mdi:speedometer"),
                dtile("sensor.sabnzbd_queue_count", "In queue", "mdi:tray-full"),
                dtile("sensor.sabnzbd_left_to_download", "Left", "mdi:progress-download")),
        section(marquee("Coming up"),
                dtile("sensor.sonarr_upcoming", "Upcoming episodes", "mdi:television-classic"),
                {"type": "calendar", "entities": ["calendar.sonarr", "calendar.radarr"], "initial_view": "listWeek"},
                span=2),
    ],
}

yard = {
    "type": "sections", "title": "Yard", "path": "yard", "icon": "mdi:sprinkler", "max_columns": 3,
    "sections": [
        section(marquee("Weather"),
                {"type": "weather-forecast", "entity": "weather.forecast_home", "forecast_type": "hourly",
                 "show_current": True, "show_forecast": True},
                dtile("binary_sensor.rachio_9207aa_rain", "Rain sensor", "mdi:weather-rainy")),
        section(marquee("Outdoor lights"),
                native_tile("light.outdoor_dimmer_light_1", "Outdoor 1", "mdi:outdoor-lamp", "light-brightness"),
                native_tile("light.outdoor_dimmer_light_2", "Outdoor 2", "mdi:outdoor-lamp", "light-brightness"),
                tile("automation.outdoor_lights_sunset_to_10_pm", "Sunset schedule", "mdi:weather-sunset", 6, "toggle")),
        section(marquee("Water now (tap a zone)"),
                tile("switch.rachio_9207aa_front_sprinklers", "Front sprinklers", "mdi:sprinkler-variant"),
                tile("switch.rachio_9207aa_back_sprinklers", "Back sprinklers", "mdi:sprinkler-variant"),
                tile("switch.rachio_9207aa_back_drip", "Back drip", "mdi:water-outline"),
                marquee("Controller"),
                tile("switch.rachio_9207aa_rain_delay", "Rain delay", "mdi:weather-pouring"),
                tile("switch.rachio_9207aa_standby", "Standby (pause all)", "mdi:pause-circle"),
                dtile("binary_sensor.rachio_9207aa_connectivity", "Rachio online", "mdi:wifi")),
        section(marquee("Schedules (tap to run)"),
                tile("switch.rachio_9207aa_front_flower_beds_schedule", "Front flower beds", "mdi:flower"),
                tile("switch.rachio_9207aa_backyard_flower_beds_schedule", "Backyard flower beds", "mdi:flower-tulip"),
                tile("switch.rachio_9207aa_back_lawn_schedule", "Back lawn", "mdi:grass")),
    ],
}

workshop = {
    "type": "sections", "title": "Workshop", "path": "workshop", "icon": "mdi:printer-3d", "max_columns": 3,
    "sections": [
        section(marquee("Icarus \u00b7 Bambu H2S"),
                {"type": "custom:ha-bambulab-print_status-card", "printer": BAMBU_PRINTER,
                 "grid_options": {"columns": "full"}},
                {"type": "custom:button-card", "template": "deco_rows", "entity": f"sensor.{P}_print_status",
                 "name": "Icarus \u00b7 H2S", "icon": "mdi:printer-3d",
                 "variables": {"rows": [
                     {"label": "Job", "entity": f"sensor.{P}_task_name"},
                     {"label": "Progress", "entity": f"sensor.{P}_print_progress", "unit": "%"},
                     {"label": "Time left", "entity": f"sensor.{P}_remaining_time", "unit": " h"},
                     {"label": "Nozzle", "entity": f"sensor.{P}_nozzle_temperature", "unit": "\u00b0", "round": 0},
                     {"label": "Bed", "entity": f"sensor.{P}_bed_temperature", "unit": "\u00b0", "round": 0},
                     {"label": "AMS humidity", "entity": f"sensor.{P}_ams_1_humidity", "unit": "%"}]},
                 "grid_options": {"columns": "full"}},
                span=2),
        section(marquee("Filament (AMS)"),
                {"type": "custom:ha-bambulab-ams-card", "ams": BAMBU_AMS, "printer": BAMBU_PRINTER,
                 "grid_options": {"columns": "full"}},
                marquee("Controls"),
                {"type": "custom:ha-bambulab-print_control-card", "printer": BAMBU_PRINTER,
                 "grid_options": {"columns": "full"}},
                tile(f"light.{P}_chamber_light", "Chamber light", "mdi:lightbulb-on-outline"),
                tile("switch.painting_desk", "Painting desk", "mdi:palette-outline")),
        section(marquee("Inkjet printer \u00b7 HP OfficeJet"),
                dtile("sensor.hp_officejet_pro_6970", "Status", "mdi:printer-outline"),
                dtile("sensor.hp_officejet_pro_6970_black_ink", "Black ink", "mdi:water"),
                dtile("sensor.hp_officejet_pro_6970_cyan_ink", "Cyan ink", "mdi:water"),
                dtile("sensor.hp_officejet_pro_6970_magenta_ink", "Magenta ink", "mdi:water"),
                dtile("sensor.hp_officejet_pro_6970_yellow_ink", "Yellow ink", "mdi:water")),
    ],
}

alexandria = {
    "type": "sections", "title": "Alexandria", "path": "alexandria", "icon": "mdi:server", "max_columns": 4,
    "sections": [
        section(marquee("Power (APC UPS)"),
                dtile("sensor.alexandria_status", "Status", "mdi:power-plug"),
                {"type": "gauge", "entity": "sensor.alexandria_battery", "name": "Battery", "min": 0, "max": 100,
                 "needle": True, "severity": {"green": 60, "yellow": 35, "red": 0}},
                {"type": "gauge", "entity": "sensor.alexandria_load", "name": "Load", "min": 0, "max": 100,
                 "needle": True, "severity": {"green": 0, "yellow": 60, "red": 80}},
                dtile("sensor.alexandria_time_left", "Runtime on battery", "mdi:timer-sand"),
                dtile("sensor.alexandria_input_voltage", "Mains voltage", "mdi:sine-wave"),
                dtile("sensor.alexandria_battery_replaced", "Battery replaced", "mdi:battery-sync")),
        section(marquee("Network"),
                dtile("binary_sensor.q1000k_router_wan_status", "Internet", "mdi:web"),
                dtile("sensor.q1000k_router_download_speed", "Download", "mdi:download-network"),
                dtile("sensor.q1000k_router_upload_speed", "Upload", "mdi:upload-network"),
                tile("switch.pi_hole", "Pi-hole ad blocking", "mdi:shield-check"),
                dtile("sensor.pi_hole_dns_queries", "DNS queries", "mdi:dns"),
                dtile("sensor.pi_hole_ads_blocked", "Ads blocked", "mdi:block-helper"),
                dtile("sensor.pi_hole_seen_clients", "Devices", "mdi:devices")),
        section(marquee("Storage and backups"),
                dtile("sensor.sabnzbd_free_disk_space", "Array free", "mdi:harddisk"),
                dtile("sensor.sabnzbd_total_disk_space", "Array size", "mdi:database"),
                dtile("sensor.backup_last_successful_automatic_backup", "Last HA backup", "mdi:backup-restore"),
                dtile("sensor.backup_next_scheduled_automatic_backup", "Next HA backup", "mdi:calendar-sync"),
                marquee("Photos (Immich)"),
                dict(dtile("sensor.immich_photos", "Photos", "mdi:image-multiple"),
                     tap_action={"action": "url", "url_path": "https://photos.salientpoint.net"}),
                dict(dtile("sensor.immich_videos", "Videos", "mdi:filmstrip-box-multiple"),
                     tap_action={"action": "url", "url_path": "https://photos.salientpoint.net"})),
        section(marquee("Last 24 hours"),
                {"type": "history-graph", "title": "UPS load and battery", "hours_to_show": 24,
                 "entities": [{"entity": "sensor.alexandria_load", "name": "Load"},
                              {"entity": "sensor.alexandria_battery", "name": "Battery"}]},
                {"type": "history-graph", "title": "Mains voltage", "hours_to_show": 24,
                 "entities": [{"entity": "sensor.alexandria_input_voltage", "name": "Volts"}]},
                {"type": "history-graph", "title": "Internet traffic", "hours_to_show": 24,
                 "entities": [{"entity": "sensor.q1000k_router_download_speed", "name": "Down"},
                              {"entity": "sensor.q1000k_router_upload_speed", "name": "Up"}]},
                span=2),
    ],
}


# ---------------------------------------------------------------- other views: headings -> marquees
DECO_TILE_DOMAINS = ("switch", "light", "sensor", "binary_sensor", "automation", "calendar")


def convert(c):
    if c.get("type") == "heading":
        return marquee(c.get("heading", ""))
    # plain tiles (no slider/feature) become Deco tiles; tiles with features keep native controls
    if c.get("type") == "tile" and not c.get("features") and c.get("entity", "").split(".")[0] in DECO_TILE_DOMAINS:
        dom = c["entity"].split(".")[0]
        action = None if dom in ("switch", "light", "automation") else "more-info"
        out = tile(c["entity"], c.get("name") or c["entity"].split(".")[1].replace("_", " ").title(),
                   c.get("icon") or "mdi:circle-outline", 6, action)
        if c.get("tap_action", {}).get("action") == "url":
            out["tap_action"] = c["tap_action"]
        return out
    return c


def decorate(view):
    view = json.loads(json.dumps(view))
    view.pop("theme", None)
    for s in view.get("sections", []):
        s["cards"] = [convert(c) for c in s.get("cards", [])]
    view.pop("badges", None) if view.get("path") == "home" else None
    return view


def main():
    dry = "--dry-run" in sys.argv
    cur = call({"type": "lovelace/config", "url_path": DASH})["result"]
    out_dir = ROOT / "dashboards"
    out_dir.mkdir(exist_ok=True)
    if not (out_dir / "home-hub.before-phase2.json").exists():
        (out_dir / "home-hub.before-phase2.json").write_text(json.dumps(cur, indent=2), encoding="utf-8")
    keep = [v for v in cur["views"] if v.get("path") == "omega7"]   # Omega-7 panel is managed by its own installer
    cfg = normalize_styles({"title": cur.get("title", "Home"), "button_card_templates": TEMPLATES,
                            "views": [home, floor, media, yard, workshop, alexandria] + keep})
    cfg = apply_cogitator(apply_seasons(cfg))
    (ROOT / "templates").mkdir(exist_ok=True)
    (ROOT / "templates" / "deco_templates.json").write_text(json.dumps(cfg["button_card_templates"], indent=2), encoding="utf-8")
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
