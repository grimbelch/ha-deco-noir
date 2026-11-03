"""Add the optional Les Saisons Home composition without replacing Deco cards."""
from copy import deepcopy
import re

HELPER = 'input_select.dashboard_theme'
THEME_NAME = 'Les Saisons'

def selector():
    return {'type':'entities', 'show_header_toggle':False,
            'entities':[{'entity':HELPER, 'name':'Theme', 'icon':'mdi:palette-outline'}],
            'grid_options':{'columns':'full'}}

def rows(items):
    return {'type':'entities', 'show_header_toggle':False,
            'entities':[{'entity':e,'name':n} for e,n in items]}

def room(title, season, position, cards):
    header = {'type':'custom:button-card', 'template':'saisons_room', 'name':title,
              'variables':{'season':season, 'position':position}}
    return {'type':'vertical-stack','cards':[header]+cards,
            'grid_options':{'columns':'full'}}

def section(*cards, span=1):
    return {'type':'grid', 'column_span':span, 'cards':list(cards),
            'visibility':[{'condition':'state','entity':HELPER,'state':THEME_NAME}]}

def apply_seasons(cfg):
    cfg = deepcopy(cfg)
    templates = cfg.setdefault('button_card_templates', {})
    # Make old cards on other tabs respect the light palette. Deco uses the exact old fallbacks.
    def palette(o):
        if isinstance(o,dict): return {k:palette(v) for k,v in o.items()}
        if isinstance(o,list): return [palette(v) for v in o]
        if isinstance(o,str) and '--seasons-' not in o:
            o=re.sub(r'rgba\(237,\s*230,\s*214,\s*[^)]+\)', lambda m:'var(--seasons-text, '+m[0]+')',o)
            o=re.sub(r'rgba\((?:14,\s*14,\s*20|11,\s*11,\s*14),\s*[^)]+\)',lambda m:'var(--seasons-surface, '+m[0]+')',o)
        return o
    cfg['button_card_templates']=templates=palette(templates)
    templates['saisons_room'] = {
        'show_icon':False, 'show_state':False, 'tap_action':{'action':'none'},
        'styles':{
            'card':[{'padding':'0'}, {'overflow':'hidden'}, {'border-radius':'90px 90px 10px 10px'},
                    {'background':'#f7e8cb'}, {'border':'1px solid #9c7651'}, {'box-shadow':'inset 0 0 0 4px #ead6b6'}],
            'grid':[{'grid-template-areas':'"art" "season" "n"'}, {'grid-template-columns':'1fr'}],
            'name':[{'font-family':'var(--deco-display)'}, {'font-size':'32px'}, {'color':'#513721'}, {'padding':'0 10px 16px'}, {'white-space':'normal'}],
            'custom_fields':{
                'art':[{'height':'190px'}, {'width':'100%'}, {'background-image':"url('/local/seasons/portraits.png?v=1')"},
                       {'background-size':'400% auto'}, {'background-position':"[[[ return variables.position + '% 18%'; ]]]"},
                       {'border-bottom':'1px solid #b39165'}],
                'season':[{'font-family':'var(--deco-display)'}, {'text-transform':'uppercase'}, {'letter-spacing':'.16em'},
                          {'font-size':'13px'}, {'color':'#835b3c'}, {'padding':'12px 0 4px'}]},
        },
        'custom_fields':{'art':' ', 'season':"[[[ return variables.season; ]]]"},
        'extra_styles':'ha-card::before, ha-card::after { display:none!important; }',
    }
    home = next(v for v in cfg['views'] if v.get('path') == 'home')
    # Idempotent: retain current Deco content, remove only sections owned by this feature.
    old = [s for s in home['sections'] if not any(c.get('state') in (THEME_NAME,'Cogitator') for c in s.get('visibility', []))]
    def replace_toggle(o):
        if isinstance(o,dict):
            if o.get('template') == 'deco_theme_toggle': return selector()
            return {k:replace_toggle(v) for k,v in o.items()}
        if isinstance(o,list): return [replace_toggle(v) for v in o]
        return o
    old = replace_toggle(old)
    for s in old:
        conditions = s.setdefault('visibility', [])
        rule = {'condition':'state','entity':HELPER,'state_not':THEME_NAME}
        if rule not in conditions: conditions.append(rule)
    # Keep actual scene actions from the existing dashboard.
    def find_scenes(o):
        found=[]
        if isinstance(o,dict):
            if o.get('template') == 'deco_scene': found.append(o)
            for v in o.values(): found.extend(find_scenes(v))
        elif isinstance(o,list):
            for v in o: found.extend(find_scenes(v))
        return found
    scenes = [{'type':'button','name':c['name'],'icon':c['icon'],'tap_action':c['tap_action'],
               'show_state':False,'icon_height':'24px'} for c in find_scenes(old)[:4]]
    top = [section({'type':'markdown','content':'# Les Saisons\nHome, through the seasons.','grid_options':{'columns':'full'}}),
           section(selector()),
           section({'type':'grid','columns':2,'square':False,'cards':scenes,'grid_options':{'columns':'full'}}),
           section({'type':'media-control','entity':'media_player.spotify','grid_options':{'columns':'full'}}),
           section({'type':'thermostat','entity':'climate.nest_thermostat','name':'Climate','grid_options':{'columns':'full'}})]
    # Title and selector share a compact row; following cards reflow naturally on phones.
    top[0]['column_span']=2
    top[1]['column_span']=2
    top[2]['column_span']=2
    p='h2s_0938ac5b0600679'
    seasonal = [
      section(room('Living Room','Spring',0,[rows([
        ('switch.couch_lamp','Couch'),('switch.chez_lounge_lamp','Chez Lounge'),('switch.pappasan_lamp','Pappasan'),
        ('switch.lamp_window','Window lamp'),('switch.grow_lamp','Grow lamp')]),
        {'type':'media-control','entity':'media_player.billie_2'}])),
      section(room('Library','Summer',100/3,[rows([
        ('switch.torch_light_front','Torch front'),('switch.torch_light_back','Torch back'),
        ('switch.basement_fireplace_lights','Fireplace')]),{'type':'media-control','entity':'media_player.library'}])),
      section(room('Outside','Autumn',200/3,[rows([
        ('light.outdoor_dimmer_light_1','Outdoor 1'),('light.outdoor_dimmer_light_2','Outdoor 2'),
        ('automation.outdoor_lights_sunset_to_10_pm','Sunset schedule'),('switch.rachio_9207aa_rain_delay','Rain delay')])])),
      section(room('Workshop','Winter',100,[
        {'type':'picture-entity','entity':f'camera.{p}_camera','show_name':False,'show_state':False},
        rows([(f'sensor.{p}_print_status','Icarus'),(f'sensor.{p}_print_progress','Progress'),
              (f'sensor.{p}_remaining_time','Time remaining'),(f'sensor.{p}_nozzle_temperature','Nozzle'),
              (f'sensor.{p}_bed_temperature','Bed'),(f'sensor.{p}_ams_1_humidity','AMS humidity')])])),
    ]
    # Preserve all additional Home content (house controls, weather, servers, etc.) in Seasons too.
    # Core scene/climate/room/workshop sections above replace only their corresponding Deco sections.
    covered={'Living Room','Library','Outside','Workshop'}
    extras=[]
    for s in old:
        cards=s.get('cards',[])
        if any(c.get('template')=='deco_room' and c.get('name') in covered for c in cards): continue
        if any(c.get('template') in ('deco_lobby','deco_scene') or c.get('type')=='thermostat' for c in cards): continue
        extra=deepcopy(s)
        extra['visibility']=[{'condition':'state','entity':HELPER,'state':THEME_NAME}]
        extras.append(extra)
    composition = {'type':'custom:saisons-home-card',
        'theme_entity':HELPER, 'music_entity':'media_player.spotify',
        'climate_entity':'climate.nest_thermostat', 'scenes':scenes,
        'rooms':[], 'grid_options':{'columns':'full'}}
    for s in seasonal:
        stack=s['cards'][0]['cards']
        header=stack[0]
        composition['rooms'].append({'title':header['name'],
            'season':header['variables']['season'],
            'position':header['variables']['position'], 'cards':stack[1:]})
    home['sections'] = old + [section(composition,span=4)] + extras
    return cfg
