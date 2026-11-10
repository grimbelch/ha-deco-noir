"""Per-user dashboard themes.

The builders still write visibility rules against the single logical helper
`input_select.dashboard_theme`. Right before saving, `to_per_user()` rewrites the
config so every person has their own helper (`input_select.dashboard_theme_<slug>`):

* every visibility / conditional rule on the helper becomes
  `or[ and[user=<id>, <rule on that user's helper>] for each user ]`
* `theme_entity` / picker `entity` become `input_select.dashboard_theme_{user}`; the
  cards resolve `{user}` from `hass.user.name` in the browser
* button-card action targets become a `[[[ ]]]` template doing the same

`from_per_user()` is the exact inverse, so the idempotent builders (apply_seasons,
apply_cogitator) can keep working on the logical form of a live config.
"""
import re
from copy import deepcopy

HELPER = 'input_select.dashboard_theme'
USER_HELPER = HELPER + '_{user}'
JS_TARGET = "[[[ return 'input_select.dashboard_theme_' + user.name.toLowerCase().replace(/[^a-z0-9]+/g, '_'); ]]]"
OPTIONS = ['Deco Noir', 'Deco Noir Lite', 'Les Saisons', 'Cogitator']
THEME_KEYS = {'Deco Noir': 'deco_noir', 'Deco Noir Lite': 'deco_noir_lite',
              'Les Saisons': 'les_saisons', 'Cogitator': 'cogitator'}


def slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower())


def helper_for(user_slug):
    return f'{HELPER}_{user_slug}'


def people(call):
    """[(user_id, slug)] for every real, active login. `call(type=...)` is a websocket call."""
    users = [u for u in call(type='config/auth/list') if not u['system_generated'] and u['is_active']]
    return sorted((u['id'], slug(u['name'])) for u in users)


def _is_helper_rule(c):
    return isinstance(c, dict) and c.get('condition') == 'state' and c.get('entity') == HELPER


def _split(conds, users):
    out, rules, at = [], [c for c in conds if _is_helper_rule(c)], None
    if not rules:
        return conds
    for c in conds:
        if _is_helper_rule(c):
            if at is None:
                at = len(out)
                out.append({'condition': 'or', 'conditions': [
                    {'condition': 'and', 'conditions': [{'condition': 'user', 'users': [uid]}] +
                     [dict(r, entity=helper_for(s)) for r in rules]}
                    for uid, s in users]})
        else:
            out.append(c)
    return out


def _is_user_group(c):
    if not (isinstance(c, dict) and c.get('condition') == 'or' and c.get('conditions')):
        return False
    for branch in c['conditions']:
        cs = branch.get('conditions', []) if branch.get('condition') == 'and' else []
        if not cs or cs[0].get('condition') != 'user':
            return False
        if not all(x.get('condition') == 'state' and str(x.get('entity', '')).startswith(HELPER + '_') for x in cs[1:]):
            return False
    return True


def _join(conds):
    out = []
    for c in conds:
        if _is_user_group(c):
            out.extend(dict(r, entity=HELPER) for r in c['conditions'][0]['conditions'][1:])
        else:
            out.append(c)
    return out


def _walk(o, fix_conds, fix_value):
    if isinstance(o, list):
        return [_walk(v, fix_conds, fix_value) for v in o]
    if not isinstance(o, dict):
        return o
    out = {}
    for k, v in o.items():
        if k == 'visibility' and isinstance(v, list):
            v = fix_conds(v)
        elif k == 'conditions' and o.get('type') == 'conditional' and isinstance(v, list):
            v = fix_conds(v)
        elif k in ('conditions',) and o.get('condition') in ('and', 'or') and isinstance(v, list):
            v = fix_conds(v)
        v = fix_value(k, v, o)
        out[k] = _walk(v, fix_conds, fix_value)
    return out


def to_per_user(cfg, users):
    assert users, 'no users to build per-user theme rules for'

    def value(k, v, parent):
        if k == 'theme_entity' and v == HELPER:
            return USER_HELPER
        if k == 'entity' and v == HELPER and parent.get('type') == 'custom:deco-theme-picker':
            return USER_HELPER
        if k == 'entity_id' and v == HELPER:
            return JS_TARGET
        if k == 'entity' and v == HELPER and 'condition' not in parent:
            raise ValueError(f'unsupported use of {HELPER} in {parent!r}; give it a per-user form')
        return v
    out = _walk(deepcopy(cfg), lambda cs: _split(cs, users), value)
    return out


def from_per_user(cfg):
    def value(k, v, parent):
        if v == USER_HELPER and k in ('theme_entity', 'entity'):
            return HELPER
        if k == 'entity_id' and v == JS_TARGET:
            return HELPER
        return v
    return _walk(deepcopy(cfg), _join, value)


def ensure_helpers(call, users, initial):
    """Create missing per-user input_selects; keep existing selections."""
    existing = {h['id']: h for h in call(type='input_select/list')}
    made = []
    for _, s in users:
        hid = f'dashboard_theme_{s}'
        if hid in existing:
            call(type='input_select/update', input_select_id=hid, name=f'Dashboard theme ({s.title()})',
                 options=OPTIONS, icon='mdi:palette-outline')
        else:
            # the id is slugified from the name, so create with a slug-shaped name, then prettify it
            r = call(type='input_select/create', name=f'Dashboard theme {s}', options=OPTIONS,
                     icon='mdi:palette-outline', initial=initial.get(s, 'Deco Noir'))
            assert r['id'] == hid, (r['id'], hid)
            call(type='input_select/update', input_select_id=hid, name=f'Dashboard theme ({s.title()})',
                 options=OPTIONS, icon='mdi:palette-outline')
            made.append(hid)
    return made
