"""Optional Cogitator composition. One full-width terminal card carries the whole Home view, so it
is configured explicitly here (same logical order as the Deco Home: scenes, music, climate,
rooms by floor, appliances) instead of being copied from the Les Saisons sections."""
from copy import deepcopy

HELPER = 'input_select.dashboard_theme'
P = 'h2s_0938ac5b0600679'

LIGHTS = ['switch.couch_lamp', 'switch.chez_lounge_lamp', 'switch.pappasan_lamp', 'switch.lamp_window',
          'switch.grow_lamp', 'switch.torch_light_front', 'switch.torch_light_back',
          'switch.basement_fireplace_lights', 'switch.grow_light_dining_room', 'switch.painting_desk',
          'light.outdoor_dimmer_light_1', 'light.outdoor_dimmer_light_2']


def rows(items):
    return {'type': 'entities', 'entities': [{'entity': e, 'name': n} for e, n in items]}


def status(items):
    """Read-only rows: (name, entity, options)."""
    out = []
    for name, entity, *opt in items:
        row = {'name': name, 'entity': entity}
        if opt:
            row.update(opt[0])
        out.append(row)
    return {'type': 'status', 'rows': out}


def cogitator_card(scenes):
    return {
        'type': 'custom:cogitator-home-card',
        'theme_entity': HELPER, 'music_entity': 'media_player.spotify',
        'climate_entity': 'climate.nest_thermostat', 'scenes': scenes,
        'purifier_entity': 'fan.air_purifier_fan',
        # Left rail: house-wide glance (replaces the old ENABLED/STANDBY counts)
        'rail': [
            {'label': 'LIGHTS ON', 'count_on': LIGHTS},
            {'label': 'UPS BATTERY', 'entity': 'sensor.alexandria_battery', 'unit': '%', 'round': 0},
            {'label': 'UPS LOAD', 'entity': 'sensor.alexandria_load', 'unit': '%', 'round': 0},
            {'label': 'WAN Mb/s', 'entity': 'sensor.q1000k_router_download_speed', 'unit': '', 'round': 0},
        ],
        # "What is running / needs attention" panel
        'systems': status([
            ('Washer', 'sensor.washer_current_status'),
            ('Dryer', 'sensor.dryer_current_status'),
            ('Icarus', f'sensor.{P}_print_status', {'progress': f'sensor.{P}_print_progress'}),
            ('Inkjet', 'sensor.hp_officejet_pro_6970'),
            ('UPS', 'sensor.alexandria_status'),
        ]),
        'rooms': [
            {'title': 'Living Room', 'cards': [
                rows([('switch.couch_lamp', 'Couch'), ('switch.chez_lounge_lamp', 'Chez Lounge'),
                      ('switch.pappasan_lamp', 'Pappasan'), ('switch.lamp_window', 'Window lamp'),
                      ('switch.grow_lamp', 'Grow lamp')]),
                {'type': 'media-control', 'entity': 'media_player.billie_2'}]},
            {'title': 'Dining & Kitchen', 'cards': [
                rows([('switch.grow_light_dining_room', 'Grow Light')]),
                {'type': 'media-control', 'entity': 'media_player.kitchen_speaker'}]},
            {'title': 'Library', 'cards': [
                rows([('switch.torch_light_front', 'Torch front'), ('switch.torch_light_back', 'Torch back'),
                      ('switch.basement_fireplace_lights', 'Fireplace')]),
                {'type': 'media-control', 'entity': 'media_player.library'}]},
            {'title': 'Craft Room', 'cards': [
                rows([('switch.painting_desk', 'Painting desk'), (f'light.{P}_chamber_light', 'Icarus chamber')])]},
            {'title': 'Outside', 'cards': [
                rows([('light.outdoor_dimmer_light_1', 'Outdoor 1'), ('light.outdoor_dimmer_light_2', 'Outdoor 2'),
                      ('automation.outdoor_lights_sunset_to_10_pm', 'Sunset schedule'),
                      ('switch.rachio_9207aa_rain_delay', 'Rain delay')])]},
            {'title': 'Weather', 'code': 'ENV / 02', 'cards': [
                status([('Now', 'weather.forecast_home', {'attr': 'temperature', 'unit': '°'}),
                        ('Sky', 'weather.forecast_home'),
                        ('Humidity', 'weather.forecast_home', {'attr': 'humidity', 'unit': '%'}),
                        ('Wind', 'weather.forecast_home', {'attr': 'wind_speed', 'unit': ' mph'}),
                        ('Rain sensor', 'binary_sensor.rachio_9207aa_rain', {'map': {'on': 'RAIN', 'off': 'DRY'}})])]},
        ],
        'grid_options': {'columns': 'full'},
    }


def apply_cogitator(cfg):
    cfg = deepcopy(cfg)
    home = next(v for v in cfg['views'] if v.get('path') == 'home')
    # Idempotent: drop previous Cogitator sections; hide every other Home section while Cogitator is selected.
    home['sections'] = [s for s in home['sections']
                        if not any(c.get('state') == 'Cogitator' for c in s.get('visibility', []))]
    seasons_card = next((c for s in home['sections'] for c in s.get('cards', [])
                         if c.get('type') == 'custom:saisons-home-card'), None)
    scenes = deepcopy(seasons_card['scenes']) if seasons_card else []
    for s in home['sections']:
        rule = {'condition': 'state', 'entity': HELPER, 'state_not': 'Cogitator'}
        if rule not in s.setdefault('visibility', []):
            s['visibility'].append(rule)
    home['sections'].append({
        'type': 'grid', 'column_span': 4, 'cards': [cogitator_card(scenes)],
        'visibility': [{'condition': 'state', 'entity': HELPER, 'state': 'Cogitator'}]})
    return cfg
