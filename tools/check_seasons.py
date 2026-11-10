"""Verify per-user theme configuration without operating household devices."""
import json, urllib.request
from ha_session import HA
from seasons_dashboard import apply_seasons
from cogitator_dashboard import apply_cogitator
from per_user_theme import people, to_per_user, from_per_user, helper_for, HELPER, USER_HELPER, JS_TARGET, OPTIONS
ha=HA()
cfg=ha.call(type='lovelace/config',url_path='home-hub')
users=people(ha.call)
logical=from_per_user(cfg)
assert to_per_user(logical,users)==cfg, 'Saved dashboard is not in per-user form for the current users'
assert apply_cogitator(apply_seasons(logical))==logical, 'Transformation must be idempotent'
assert f'"{HELPER}"' not in json.dumps(cfg), 'Dashboard still references the shared theme helper'
print('Per-user rules for:',[s for _,s in users])
for _,s in users:
    st=ha.rest('states/'+helper_for(s))
    assert st['attributes']['options']==OPTIONS, (s,st['attributes']['options'])
    print(' ',helper_for(s),'=',st['state'])
autos=[a for a in ha.call(type='get_states') if a['entity_id'].startswith('automation.')]
assert not any(a['attributes'].get('id')=='dashboard_theme_apply' for a in autos), 'Server-wide theme automation is back'
resources=[r['url'] for r in ha.call(type='lovelace/resources')]
assert any(u.startswith('/local/deco/theme-sync.js') for u in resources), 'theme-sync.js resource missing'
states={s['entity_id'] for s in ha.call(type='get_states')}
refs=set()
def walk(o):
    if isinstance(o,dict):
        if isinstance(o.get('entity'),str): refs.add(o['entity'])
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(cfg)
missing=sorted(refs-states-{USER_HELPER,JS_TARGET})
print('Missing entity references:',missing)
assert not missing
with urllib.request.urlopen('http://192.168.0.200/local/seasons/portraits.png',timeout=30) as r:
    assert r.read(8)==b'\x89PNG\r\n\x1a\n'
    print('Portrait asset served:',r.status)
with urllib.request.urlopen('http://192.168.0.200/local/deco/theme-sync.js',timeout=30) as r:
    assert b'settheme' in r.read(); print('theme-sync.js served:',r.status)
