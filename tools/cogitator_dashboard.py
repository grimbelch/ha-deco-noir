"""Optional Cogitator composition, using the same real devices as Seasons."""
from copy import deepcopy

def apply_cogitator(cfg):
    cfg=deepcopy(cfg)
    home=next(v for v in cfg['views'] if v.get('path')=='home')
    home['sections']=[s for s in home['sections'] if not any(c.get('state')=='Cogitator' for c in s.get('visibility',[]))]
    seasons=[]
    for s in home['sections']:
        if any(c.get('state')=='Les Saisons' for c in s.get('visibility',[])):
            seasons.append(s)
        else:
            rule={'condition':'state','entity':'input_select.dashboard_theme','state_not':'Cogitator'}
            if rule not in s.setdefault('visibility',[]): s['visibility'].append(rule)
    for s in seasons:
        new=deepcopy(s)
        new['visibility']=[{'condition':'state','entity':'input_select.dashboard_theme','state':'Cogitator'}]
        for card in new.get('cards',[]):
            if card.get('type')=='custom:saisons-home-card':
                card['type']='custom:cogitator-home-card'
        home['sections'].append(new)
    return cfg
