"""Verify theme selection and configuration without operating household devices."""
import time, urllib.request
from ha_session import HA
from seasons_dashboard import apply_seasons
ha=HA()
cfg=ha.call(type='lovelace/config',url_path='home-hub')
assert apply_seasons(cfg)==cfg, 'Transformation must be idempotent'
helper=ha.call(type='input_select/list')
print('Theme helper:',next(h for h in helper if h['name']=='Dashboard theme'))
start=ha.rest('states/input_select.dashboard_theme')['state']
try:
    for choice,name in [('Les Saisons','les_saisons'),('Deco Noir Lite','deco_noir_lite'),('Deco Noir','deco_noir')]:
        ha.rest('services/input_select/select_option',{'entity_id':'input_select.dashboard_theme','option':choice})
        for _ in range(20):
            themes=ha.call(type='frontend/get_themes')
            if themes.get('default_theme')==name and themes.get('default_dark_theme')==name: break
            time.sleep(.25)
        assert themes.get('default_theme')==name and themes.get('default_dark_theme')==name, (choice,themes.get('default_theme'),themes.get('default_dark_theme'))
        print('Theme selection works:',choice)
finally:
    ha.rest('services/input_select/select_option',{'entity_id':'input_select.dashboard_theme','option':start})
states={s['entity_id'] for s in ha.call(type='get_states')}
refs=set()
def walk(o):
    if isinstance(o,dict):
        if isinstance(o.get('entity'),str): refs.add(o['entity'])
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(cfg)
print('Missing entity references:',sorted(refs-states))
assert not refs-states
with urllib.request.urlopen('http://192.168.0.200/local/seasons/portraits.png',timeout=30) as r:
    assert r.read(8)==b'\x89PNG\r\n\x1a\n'
    print('Portrait asset served:',r.status)
print('Restored selection:',start)
