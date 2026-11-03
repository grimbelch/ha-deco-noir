"""Back up and install the optional Seasons dashboard; assets/theme must be copied first."""
import datetime, json, pathlib, sys
from ha_session import HA
from seasons_dashboard import apply_seasons
from cogitator_dashboard import apply_cogitator

ROOT=pathlib.Path(__file__).resolve().parent.parent
ha=HA()
cfg=ha.call(type='lovelace/config',url_path='home-hub')
helper=next(x for x in ha.call(type='input_select/list') if x['name']=='Dashboard theme')
current=ha.rest('states/input_select.dashboard_theme')['state']
automation=ha.rest('config/automation/config/dashboard_theme_apply')
backup=ROOT/'build'/('before-seasons-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
for name,value in [('dashboard',cfg),('helper',helper),('automation',automation),('selection',current)]:
    (backup/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')
out=apply_cogitator(apply_seasons(cfg))
resources=ha.call(type='lovelace/resources')
(backup/'resources.json').write_text(json.dumps(resources,indent=2),encoding='utf-8')
for resource_url in ['/local/seasons/seasons-card.js?v=6','/local/cogitator/cogitator-card.js?v=3']:
    existing=next((r for r in resources if r['url'].split('?')[0]==resource_url.split('?')[0]),None)
    if existing:
        ha.call(type='lovelace/resources/update',resource_id=existing['id'],url=resource_url,res_type='module')
    else:
        ha.call(type='lovelace/resources/create',url=resource_url,res_type='module')
# Only palette/layout settings are changed; never call device-control services here.
ha.rest('services/frontend/reload_themes',{})
assert 'les_saisons' in ha.call(type='frontend/get_themes')['themes'], 'Theme not installed'
assert 'cogitator' in ha.call(type='frontend/get_themes')['themes'], 'Cogitator theme not installed'
ha.call(type='input_select/update',input_select_id=helper['id'],name='Dashboard theme',options=['Deco Noir','Deco Noir Lite','Les Saisons','Cogitator'])
new_automation={
 'alias':'Dashboard theme: apply selection','description':'Apply the optional dashboard theme in both browser color modes; restore on restart.',
 'mode':'restart',
 'triggers':[{'trigger':'state','entity_id':'input_select.dashboard_theme'}, {'trigger':'homeassistant','event':'start'}],
 'actions':[{'action':'frontend.set_theme','data':{
     'name':"{{ {'Deco Noir':'deco_noir','Deco Noir Lite':'deco_noir_lite','Les Saisons':'les_saisons','Cogitator':'cogitator','deco_noir':'deco_noir','deco_noir_lite':'deco_noir_lite'}.get(states('input_select.dashboard_theme'), 'deco_noir') }}",
     'mode':mode}} for mode in ['light','dark']]}
ha.rest('config/automation/config/dashboard_theme_apply',new_automation)
ha.rest('services/automation/reload',{})
ha.call(type='lovelace/config/save',url_path='home-hub',config=out)
# Leave the user's existing visual choice selected; new theme is optional.
choice={'deco_noir':'Deco Noir','deco_noir_lite':'Deco Noir Lite'}.get(current,current)
if '--select-cogitator' in sys.argv: choice='Cogitator'
ha.rest('services/input_select/select_option',{'entity_id':'input_select.dashboard_theme','option':choice})
name={'Deco Noir':'deco_noir','Deco Noir Lite':'deco_noir_lite','Les Saisons':'les_saisons','Cogitator':'cogitator'}[choice]
for mode in ['light','dark']: ha.rest('services/frontend/set_theme',{'name':name,'mode':mode})
(ROOT/'dashboards'/'home-hub.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(ROOT/'templates'/'deco_templates.json').write_text(json.dumps(out['button_card_templates'],indent=2),encoding='utf-8')
saved=ha.call(type='lovelace/config',url_path='home-hub')
assert saved==out
print('Saved and read back dashboard; backup:',backup)
print('Selector:',ha.rest('states/input_select.dashboard_theme')['attributes']['options'])
print('Current selection:',choice)
