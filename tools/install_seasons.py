"""Back up and install the Seasons/Cogitator compositions with per-user themes; assets must be copied first.

Each person has their own `input_select.dashboard_theme_<name>`; the dashboard's theme rules are
rewritten per user (see per_user_theme.py) and www/deco/theme-sync.js applies the choice to that
user only. `--select-cogitator` switches the token owner's own theme to Cogitator.
"""
import datetime, json, pathlib, sys, urllib.request
from ha_session import HA
from seasons_dashboard import apply_seasons
from cogitator_dashboard import apply_cogitator
from per_user_theme import people, to_per_user, from_per_user, ensure_helpers, helper_for, slug, OPTIONS

ROOT=pathlib.Path(__file__).resolve().parent.parent
ha=HA()

def delete(path):
    req=urllib.request.Request(ha.url+'/api/'+path,headers={'Authorization':'Bearer '+ha.token},method='DELETE')
    with urllib.request.urlopen(req,timeout=40) as r: return json.load(r)

cfg=ha.call(type='lovelace/config',url_path='home-hub')
users=people(ha.call)
helpers=ha.call(type='input_select/list')
states={s['entity_id']:s['state'] for s in ha.call(type='get_states')}
legacy=states.get('input_select.dashboard_theme')          # the old shared helper, if still present
try: automation=ha.rest('config/automation/config/dashboard_theme_apply')
except Exception: automation=None                          # already retired
backup=ROOT/'build'/('before-seasons-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
selection={k:v for k,v in states.items() if k.startswith('input_select.dashboard_theme')}
for name,value in [('dashboard',cfg),('helpers',helpers),('automation',automation),('selection',selection)]:
    (backup/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')
out=to_per_user(apply_cogitator(apply_seasons(from_per_user(cfg))),users)
resources=ha.call(type='lovelace/resources')
(backup/'resources.json').write_text(json.dumps(resources,indent=2),encoding='utf-8')
for resource_url in ['/local/seasons/seasons-card.js?v=8','/local/cogitator/cogitator-card.js?v=9',
                     '/local/deco/deco-theme-picker.js?v=5','/local/deco/theme-sync.js?v=1']:
    existing=next((r for r in resources if r['url'].split('?')[0]==resource_url.split('?')[0]),None)
    if existing:
        ha.call(type='lovelace/resources/update',resource_id=existing['id'],url=resource_url,res_type='module')
    else:
        ha.call(type='lovelace/resources/create',url=resource_url,res_type='module')
# Only palette/layout settings are changed; never call device-control services here.
ha.rest('services/frontend/reload_themes',{})
assert 'les_saisons' in ha.call(type='frontend/get_themes')['themes'], 'Theme not installed'
assert 'cogitator' in ha.call(type='frontend/get_themes')['themes'], 'Cogitator theme not installed'
# New helpers start from the old shared choice (what everyone saw until now); Guest starts on Deco Noir.
start=legacy if legacy in OPTIONS else 'Deco Noir'
made=ensure_helpers(ha.call,users,{s:(start if s!='guest' else 'Deco Noir') for _,s in users})
ha.call(type='lovelace/config/save',url_path='home-hub',config=out)
saved=ha.call(type='lovelace/config',url_path='home-hub')
assert saved==out
# Retire server-wide theme switching: it changed the theme for every user at once.
if automation:
    delete('config/automation/config/dashboard_theme_apply'); ha.rest('services/automation/reload',{})
if any(h['id']=='dashboard_theme' for h in helpers):
    ha.call(type='input_select/delete',input_select_id='dashboard_theme')
if '--select-cogitator' in sys.argv:
    me=ha.call(type='auth/current_user')
    ha.rest('services/input_select/select_option',{'entity_id':helper_for(slug(me['name'])),'option':'Cogitator'})
(ROOT/'dashboards'/'home-hub.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(ROOT/'templates'/'deco_templates.json').write_text(json.dumps(out['button_card_templates'],indent=2),encoding='utf-8')
print('Saved and read back dashboard; backup:',backup)
print('Created helpers:',made or 'none (all existed)')
for _,s in users: print(' ',helper_for(s),'=',ha.rest('states/'+helper_for(s))['state'])
