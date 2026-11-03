"""Deco Noir button-card templates (Phase 2).

Exported as TEMPLATES (dict) and written to templates/deco_templates.json by build_dashboard.py.
Every template relies on the deco_noir theme variables (--deco-*).
"""

PLAIN = {"class": "deco-plain"}

# Shared CSS for HTML rendered inside custom_fields
EXTRA = """
.mq{display:flex;align-items:center;gap:12px;width:100%}
.mq .r{flex:1;height:5px;border-top:1px solid var(--deco-hair);border-bottom:1px solid var(--deco-hair-faint)}
.mq .t{font-family:var(--deco-display);font-size:19px;letter-spacing:.14em;text-transform:uppercase;color:var(--deco-gold-hi);white-space:nowrap}
.mq .d{font-size:8px;color:var(--deco-gold);margin:0 10px;vertical-align:middle}
.chip{display:inline-flex;align-items:center;gap:6px;padding:6px 11px 6px 8px;border:1px solid var(--deco-hair-faint);background:rgba(255,255,255,.02);
  font:400 10px/1 var(--deco-label);letter-spacing:.18em;text-transform:uppercase;color:rgba(237,230,214,.6);white-space:nowrap}
.chip b{font-weight:600;color:var(--deco-ivory);letter-spacing:.12em}
.chip ha-icon{--mdc-icon-size:15px;color:var(--deco-gold)}
.chip.ok ha-icon{color:var(--deco-emerald)}
.chip.bad ha-icon{color:var(--deco-garnet)}
"""

ART = {
    "living": '<svg viewBox="0 0 300 92" preserveAspectRatio="xMaxYMax meet" style="stroke:var(--deco-gold);fill:none;stroke-opacity:.5">'
              '<path d="M150 92 V40 h20 V28 h20 V16 h40 v12 h20 v12 h20 v52"/><path d="M170 92 V48 h20 V36 h80 v12 h20 v44"/>'
              '<path d="M200 92 V60 a30 30 0 0 1 60 0 V92"/></svg>',
    "library": '<svg viewBox="0 0 300 92" preserveAspectRatio="xMaxYMax meet" style="stroke:var(--deco-gold);fill:none;stroke-opacity:.5">'
               '<path d="M200 92 V30 a40 40 0 0 1 80 0 V92"/><path d="M212 92 V34 a28 28 0 0 1 56 0 V92"/>'
               '<path d="M240 6 V92"/><path d="M212 50 H268 M212 68 H268"/></svg>',
    "outside": '<svg viewBox="0 0 300 92" preserveAspectRatio="xMaxYMax meet" style="stroke:var(--deco-gold);fill:none;stroke-opacity:.5">'
               '<path d="M190 92 L240 20 L290 92"/><path d="M205 92 L240 42 L275 92"/>'
               '<path d="M240 20 V8 M226 14 l14 -6 14 6"/><path d="M150 92 h150"/></svg>',
    "house": '<svg viewBox="0 0 300 92" preserveAspectRatio="xMaxYMax meet" style="stroke:var(--deco-gold);fill:none;stroke-opacity:.5">'
             '<path d="M190 92 V44 L240 14 L290 44 V92"/><path d="M204 92 V50 L240 28 L276 50 V92"/>'
             '<path d="M228 92 V66 h24 V92"/><path d="M150 92 h150"/></svg>',
    "workshop": '<svg viewBox="0 0 300 92" preserveAspectRatio="xMaxYMax meet" style="stroke:var(--deco-gold);fill:none;stroke-opacity:.5">'
                '<path d="M196 92 V26 h88 V92"/><path d="M206 92 V36 h68 V92"/><path d="M220 80 h40 M228 70 h24 M236 60 h8"/>'
                '<path d="M240 26 V12 M226 12 h28"/></svg>',
}

WX_ICON_JS = """const map={'clear-night':'weather-night','cloudy':'weather-cloudy','fog':'weather-fog','hail':'weather-hail',
'lightning':'weather-lightning','lightning-rainy':'weather-lightning-rainy','partlycloudy':'weather-partly-cloudy',
'pouring':'weather-pouring','rainy':'weather-rainy','snowy':'weather-snowy','snowy-rainy':'weather-snowy-rainy',
'sunny':'weather-sunny','windy':'weather-windy','windy-variant':'weather-windy-variant','exceptional':'alert-circle-outline'};"""

TEMPLATES = {
    # ------------------------------------------------------------ marquee heading
    "deco_marquee": {
        "card_mod": PLAIN,
        "show_icon": False, "show_name": False, "show_state": False,
        "tap_action": {"action": "none"}, "hold_action": {"action": "none"},
        "extra_styles": EXTRA,
        "custom_fields": {
            "m": "[[[ return `<div class='mq'><span class='r'></span><span class='t'><span class='d'>◆</span>${variables.title}<span class='d'>◆</span></span><span class='r'></span></div>`; ]]]"
        },
        "styles": {
            "card": ["background: none", "border: none", "box-shadow: none", "padding: 14px 2px 4px", "overflow: visible"],
            "grid": ["grid-template-areas: '\"m\"'", "grid-template-columns: 1fr"],
            "custom_fields": {"m": ["width: 100%"]},
        },
        "variables": {"title": "Section"},
    },

    # ------------------------------------------------------------ deco tile (diamond well)
    "deco_tile": {
        "show_state": True,
        "tap_action": {"action": "toggle", "haptic": "light"},
        "hold_action": {"action": "more-info"},
        "state_display": "[[[ if (entity && entity.state === 'on' && entity.attributes.brightness) return Math.round(entity.attributes.brightness/2.55) + '%'; if (entity && entity.attributes.volume_level !== undefined && entity.state !== 'off') return (entity.state.charAt(0).toUpperCase()+entity.state.slice(1)) + ' · ' + Math.round(entity.attributes.volume_level*100) + '%'; return helpers.localize(entity); ]]]",
        "styles": {
            "card": ["padding: 12px 12px 11px", "height: 100%", "box-sizing: border-box", "border-radius: 0",
                     "transition: box-shadow .3s ease, background .3s ease"],
            "grid": ["grid-template-areas: '\"i\" \"n\" \"s\"'", "grid-template-rows: 44px min-content min-content",
                     "grid-template-columns: 1fr", "justify-items: start", "align-items: center"],
            "img_cell": ["width: 32px", "height: 32px", "margin-left: 6px", "transform: rotate(45deg)",
                         "border: 1px solid var(--deco-hair-faint)", "background: rgba(255,255,255,.015)"],
            "icon": ["transform: rotate(-45deg)", "width: 18px", "color: rgba(237,230,214,.45)"],
            "name": ["font-family: var(--deco-label)", "font-size: 11px", "letter-spacing: .1em", "text-transform: uppercase",
                     "color: rgba(237,230,214,.6)", "justify-self: start", "margin-top: 8px", "white-space: nowrap",
                     "overflow: hidden", "text-overflow: ellipsis", "max-width: 100%"],
            "state": ["font-family: var(--deco-num)", "font-size: 12px", "color: rgba(237,230,214,.52)", "justify-self: start",
                      "margin-top: 3px", "letter-spacing: .04em"],
        },
        "state": [
            {"value": "on", "styles": {
                "card": ["border-color: rgba(201,164,76,.55)",
                         "background: radial-gradient(120% 90% at 20% 0%, rgba(201,164,76,.22), rgba(201,164,76,.04) 60%, transparent), var(--ha-card-background)",
                         "box-shadow: 0 0 22px rgba(201,164,76,.18), inset 0 0 0 1px rgba(201,164,76,.14)"],
                "img_cell": ["border-color: var(--deco-gold)", "background: rgba(201,164,76,.14)", "box-shadow: 0 0 14px rgba(201,164,76,.35)"],
                "icon": ["color: var(--deco-gold-hi)"],
                "name": ["color: var(--deco-ivory)"],
                "state": ["color: var(--deco-gold-hi)"]}},
            {"value": "playing", "id": "playing", "styles": {
                "card": ["border-color: rgba(201,164,76,.55)", "box-shadow: 0 0 22px rgba(201,164,76,.14)"],
                "img_cell": ["border-color: var(--deco-gold)", "background: rgba(201,164,76,.14)"],
                "icon": ["color: var(--deco-gold-hi)"], "name": ["color: var(--deco-ivory)"], "state": ["color: var(--deco-gold-hi)"]}},
            {"value": "unavailable", "styles": {"card": ["opacity: .45"]}},
        ],
    },

    # ------------------------------------------------------------ scene button
    "deco_scene": {
        "show_state": False,
        "hold_action": {"action": "none"},
        "styles": {
            "card": ["padding: 14px 6px 12px", "height: 100%", "min-height: 100px", "box-sizing: border-box"],
            "grid": ["grid-template-areas: '\"i\" \"n\"'", "grid-template-rows: 40px min-content", "align-content: center"],
            "img_cell": ["height: 40px", "width: 40px", "justify-self: center"],
            "icon": ["width: 28px", "color: var(--deco-gold-hi)"],
            "name": ["font-family: var(--deco-label)", "font-size: 10px", "letter-spacing: .2em", "text-transform: uppercase",
                     "color: rgba(237,230,214,.62)", "margin-top: 8px", "white-space: normal", "line-height: 1.3"],
        },
    },

    # ------------------------------------------------------------ grand lobby header
    "deco_lobby": {
        "entity": "sensor.time",
        "show_icon": False, "show_name": False, "show_state": False,
        "tap_action": {"action": "none"}, "hold_action": {"action": "none"},
        "triggers_update": ["sensor.time", "weather.forecast_home", "sensor.alexandria_status", "sensor.alexandria_battery",
                            "switch.pi_hole", "sensor.sabnzbd_status", "sensor.h2s_0938ac5b0600679_print_status",
                            "climate.nest_thermostat"],
        "extra_styles": EXTRA + """
.clk{font:200 64px/.9 var(--deco-num);color:var(--deco-ivory);letter-spacing:.02em}
.clk small{font:300 16px var(--deco-label);letter-spacing:.3em;color:var(--deco-gold-hi);margin-left:6px}
.dt{font:400 11px/1 var(--deco-label);letter-spacing:.38em;text-transform:uppercase;color:var(--deco-gold-hi);margin-top:12px}
.gr{font:400 26px/1.1 var(--deco-display);color:var(--deco-ivory);margin-top:8px}
.wx{text-align:right}
.wx ha-icon{--mdc-icon-size:44px;color:var(--deco-gold-hi)}
.wx .t{font:200 40px/1 var(--deco-num);color:var(--deco-ivory)}
.wx .c{font:400 10px/1.5 var(--deco-label);letter-spacing:.26em;text-transform:uppercase;color:rgba(237,230,214,.6)}
.chips{display:flex;flex-wrap:wrap;gap:8px;border-top:1px solid var(--deco-hair-faint);padding-top:14px;margin-top:14px}
@media (max-width:600px){.clk{font-size:52px}.gr{font-size:22px}#container{grid-template-areas:'left' 'right' 'chips' !important;grid-template-columns:1fr !important}#right{justify-self:start !important;margin-top:10px}.wx{text-align:left;display:flex;align-items:center;gap:12px}.wx ha-icon{--mdc-icon-size:34px}.wx .t{font-size:32px}}
""",
        "custom_fields": {
            "left": """[[[
const d=new Date(); let h=d.getHours(); const m=String(d.getMinutes()).padStart(2,'0');
const ap=h>=12?'PM':'AM'; h=h%12||12;
const days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const months=['January','February','March','April','May','June','July','August','September','October','November','December'];
const hr=d.getHours(); const part= hr<5?'Good night':hr<12?'Good morning':hr<17?'Good afternoon':'Good evening';
const who=(user && user.name) ? user.name.split(' ')[0] : '';
return `<div class="clk">${h}:${m}<small>${ap}</small></div><div class="dt">${days[d.getDay()]} · ${months[d.getMonth()]} ${d.getDate()}</div><div class="gr">${part}${who?', '+who:''}</div>`;
]]]""",
            "right": """[[[
""" + WX_ICON_JS + """
const w=states['weather.forecast_home']; if(!w) return '';
const ic=map[w.state]||'weather-cloudy';
const cond=w.state==='partlycloudy'?'Partly cloudy':w.state.replace(/-/g,' ');
const t=Math.round(w.attributes.temperature); const u=w.attributes.temperature_unit||'°';
const th=states['climate.nest_thermostat']; const inside= th && th.attributes.current_temperature!==undefined ? ` · Inside ${Math.round(th.attributes.current_temperature)}°` : '';
return `<div class="wx"><ha-icon icon="mdi:${ic}"></ha-icon><div class="t">${t}°</div><div class="c">${cond}${inside}</div></div>`;
]]]""",
            "chips": """[[[
const s=(e)=>states[e]?states[e].state:'unknown';
const ups=s('sensor.alexandria_status'); const batt=Math.round(parseFloat(s('sensor.alexandria_battery')));
const onb=ups.includes('ONBATT');
const chip=(cls,icon,label,val)=>`<span class="chip ${cls}"><ha-icon icon="${icon}"></ha-icon>${label} <b>${val}</b></span>`;
const pr=s('sensor.h2s_0938ac5b0600679_print_status');
const prl={finish:'Finished',running:'Printing',pause:'Paused',failed:'Failed',idle:'Idle',prepare:'Preparing'}[pr]||pr;
let out=chip(onb?'bad':'ok','mdi:lightning-bolt','Power',onb?`On battery · ${batt}%`:`On mains · ${batt}%`);
out+=chip(s('switch.pi_hole')==='on'?'ok':'bad','mdi:shield-check-outline','Ad blocking',s('switch.pi_hole')==='on'?'On':'Off');
out+=chip('','mdi:download-outline','Downloads',s('sensor.sabnzbd_status'));
out+=chip(pr==='failed'?'bad':(pr==='finish'?'ok':''),'mdi:printer-3d','Icarus',prl);
return `<div class="chips">${out}</div>`;
]]]""",
        },
        "styles": {
            "card": ["padding: 22px 22px 18px"],
            "grid": ["grid-template-areas: '\"left right\" \"chips chips\"'", "grid-template-columns: 1fr auto",
                     "align-items: end"],
            "custom_fields": {"left": ["justify-self: start", "text-align: left"], "right": ["justify-self: end"],
                              "chips": ["justify-self: stretch"]},
        },
    },

    # ------------------------------------------------------------ room banner
    "deco_room": {
        "show_icon": False, "show_state": False,
        "tap_action": {"action": "navigate", "navigation_path": "/home-hub/floor-plan"},
        "hold_action": {"action": "none"},
        "triggers_update": "all",
        "custom_fields": {
            "art": "[[[ return variables.art_svg || ''; ]]]",
            "meta": """[[[
const lamps=variables.lamps||[]; const on=lamps.filter(e=>states[e]&&states[e].state==='on').length;
let l1= lamps.length ? (on===0?'<b>All off</b>':`<b>${on} of ${lamps.length}</b> on`) : '';
let l2=''; if(variables.line2_entity && states[variables.line2_entity]){ const st=states[variables.line2_entity];
  let v=helpers.localize(st); if(variables.line2_attr) v=st.attributes[variables.line2_attr]; l2=`${variables.line2_label} · ${v}${variables.line2_unit||''}`; }
return `${l1}${l1&&l2?'<br>':''}${l2}`;
]]]""",
        },
        "styles": {
            "card": ["padding: 0 18px 12px", "height: 100%", "min-height: 92px", "box-sizing: border-box", "overflow: hidden",
                     "background: linear-gradient(180deg, rgba(14,14,20,.35), rgba(14,14,20,.62))"],
            "grid": ["grid-template-areas: '\"n meta\"'", "grid-template-columns: 1fr auto", "align-items: end", "height: 100%"],
            "name": ["font-family: var(--deco-display)", "font-size: 26px", "letter-spacing: .06em", "color: var(--deco-ivory)",
                     "justify-self: start", "z-index: 1", "align-self: end", "white-space: nowrap", "overflow: hidden",
                     "text-overflow: ellipsis", "max-width: 100%", "padding-right: 10px"],
            "custom_fields": {
                "art": ["position: absolute", "right: 0", "bottom: 0", "width: 300px", "height: 92px", "opacity: .55", "pointer-events: none"],
                "meta": ["font-family: var(--deco-label)", "font-size: 10px", "line-height: 1.7", "letter-spacing: .22em",
                         "text-transform: uppercase", "color: rgba(237,230,214,.62)", "text-align: right", "z-index: 1",
                         "text-shadow: 0 1px 8px rgba(0,0,0,.9)", "align-self: end",
                         "background: rgba(11,11,14,.78)", "padding: 5px 9px", "border: 1px solid var(--deco-hair-faint)",
                         "white-space: nowrap"],
            },
        },
        "extra_styles": ".meta b,#meta b{color:var(--deco-gold-hi);font-weight:600} b{color:var(--deco-gold-hi);font-weight:600}"
                        " ha-card::before{content:'';position:absolute;left:0;right:0;bottom:0;height:2px;"
                        "background:linear-gradient(90deg,transparent,var(--room-accent,var(--deco-gold)),transparent);opacity:.85}",
        "variables": {"lamps": [], "art_svg": ""},
    },

    # ------------------------------------------------------------ gauge
    "deco_gauge": {
        "show_icon": False, "show_state": False,
        "tap_action": {"action": "more-info"},
        "custom_fields": {
            "g": """[[[
const v=Math.max(0,Math.min(100,parseFloat(entity.state)||0)); const L=201; const dash=(v/100*L).toFixed(1);
return `<svg viewBox="0 0 160 96" style="width:100%;max-width:170px;display:block;margin:0 auto">
<path d="M16 86 A64 64 0 0 1 144 86" fill="none" style="stroke:rgba(201,164,76,.16)" stroke-width="6"/>
<path d="M16 86 A64 64 0 0 1 144 86" fill="none" style="stroke:var(--deco-gold)" stroke-width="6" stroke-dasharray="${dash} ${L}"/>
<path d="M8 86 A72 72 0 0 1 152 86" fill="none" style="stroke:rgba(201,164,76,.35)" stroke-width="1"/>
<g style="stroke:rgba(201,164,76,.5)"><path d="M80 10 v8"/><path d="M24 30 l6 6"/><path d="M136 30 l-6 6"/></g></svg>
<div style="font:200 30px/1 var(--deco-num);color:var(--deco-ivory);margin-top:-28px">${Math.round(v)}<span style="font-size:13px;color:var(--deco-gold-hi)">%</span></div>`;
]]]"""},
        "styles": {
            "card": ["padding: 14px 10px 14px"],
            "grid": ["grid-template-areas: '\"g\" \"n\"'", "grid-template-rows: auto min-content"],
            "name": ["font-family: var(--deco-label)", "font-size: 10px", "letter-spacing: .28em", "text-transform: uppercase",
                     "color: rgba(237,230,214,.62)", "margin-top: 10px", "white-space: normal"],
        },
    },

    # ------------------------------------------------------------ stat rows (printer etc.)
    "deco_rows": {
        "show_icon": True, "show_state": False,
        "tap_action": {"action": "more-info"},
        "triggers_update": "all",
        "extra_styles": """
.rows{width:100%}
.row{display:flex;justify-content:space-between;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--deco-hair-faint)}
.row:last-child{border-bottom:0}
.row span{font:400 10px/1 var(--deco-label);letter-spacing:.24em;text-transform:uppercase;color:rgba(237,230,214,.6)}
.row b{font:300 17px/1 var(--deco-num);color:var(--deco-ivory);font-weight:300;max-width:62%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge{font:600 9px/1 var(--deco-label);letter-spacing:.24em;text-transform:uppercase;padding:6px 9px;border:1px solid var(--deco-gold);color:var(--deco-gold-hi)}
.badge.ok{border-color:var(--deco-emerald);color:var(--deco-emerald)} .badge.bad{border-color:var(--deco-garnet);color:var(--deco-garnet)}
""",
        "custom_fields": {
            "badge": """[[[
if(!entity) return ''; const v=entity.state;
const lab={finish:'Finished',running:'Printing',pause:'Paused',failed:'Failed',idle:'Idle',prepare:'Preparing',offline:'Offline'}[v]||v;
const cls=v==='finish'?'ok':(v==='failed'||v==='offline'?'bad':'');
return `<span class="badge ${cls}">${lab}</span>`;
]]]""",
            "rows": """[[[
const rows=variables.rows||[]; let h='<div class="rows">';
for(const r of rows){ const st=states[r.entity]; if(!st) continue; let v=r.attr?st.attributes[r.attr]:st.state;
  const num=parseFloat(v); if(r.round!==undefined && !isNaN(num)) v=num.toFixed(r.round);
  h+=`<div class="row"><span>${r.label}</span><b>${v}${r.unit?`<em style="font-style:normal;font-size:12px;color:var(--deco-gold-hi);margin-left:2px">${r.unit}</em>`:''}</b></div>`; }
return h+'</div>';
]]]""",
        },
        "styles": {
            "card": ["padding: 16px 18px 10px"],
            "grid": ["grid-template-areas: '\"i n badge\" \"rows rows rows\"'", "grid-template-columns: 34px 1fr auto",
                     "align-items: center", "column-gap: 10px"],
            "icon": ["width: 26px", "color: var(--deco-gold-hi)"],
            "name": ["font-family: var(--deco-display)", "font-size: 22px", "letter-spacing: .05em", "justify-self: start",
                     "color: var(--deco-ivory)"],
            "custom_fields": {"rows": ["margin-top: 6px"]},
        },
        "variables": {"rows": []},
    },

    # ------------------------------------------------------------ floor plan marker
    "deco_marker": {
        "card_mod": PLAIN,
        # deco-marker-mobile: on phones show only the diamond (labels crowd the living room)
        "extra_styles": "ha-card::after, ha-card::before { display: none !important; } @media (max-width: 600px) { #name { display: none !important; } ha-card { width: 30px !important; } }",
        "show_state": False,
        "tap_action": {"action": "toggle", "haptic": "light"},
        "hold_action": {"action": "more-info"},
        "styles": {
            "card": ["background: none", "border: none", "box-shadow: none", "padding: 0", "overflow: visible", "width: 58px",
                     "-webkit-backdrop-filter: none", "backdrop-filter: none"],
            "grid": ["grid-template-areas: '\"i\" \"n\"'", "grid-template-rows: 34px auto", "justify-items: center"],
            "img_cell": ["width: 24px", "height: 24px", "transform: rotate(45deg)", "border: 1px solid var(--deco-gold)",
                         "background: rgba(11,11,14,.82)", "transition: box-shadow .4s ease, background .4s ease"],
            "icon": ["transform: rotate(-45deg)", "width: 14px", "color: rgba(237,230,214,.55)"],
            "name": ["font-family: var(--deco-label)", "font-size: 8px", "letter-spacing: .12em", "text-transform: uppercase",
                     "color: rgba(237,230,214,.72)", "white-space: nowrap", "margin-top: 2px",
                     "text-shadow: 0 1px 4px #000, 0 0 2px #000"],
        },
        "state": [
            {"value": "on", "styles": {
                "img_cell": ["background: rgba(201,164,76,.32)",
                             "box-shadow: 0 0 14px 4px rgba(230,207,154,.55), 0 0 46px 22px rgba(201,164,76,.22)"],
                "icon": ["color: #FFF4D6"], "name": ["color: var(--deco-gold-hi)"]}},
            {"value": "playing", "styles": {
                "img_cell": ["background: rgba(201,164,76,.25)", "box-shadow: 0 0 12px 3px rgba(230,207,154,.4)"],
                "icon": ["color: var(--deco-gold-hi)"]}},
            {"value": "heat", "styles": {"img_cell": ["border-color: #D9824A", "box-shadow: 0 0 12px 3px rgba(217,130,74,.35)"],
                                         "icon": ["color: #F0B489"]}},
            {"value": "cool", "styles": {"img_cell": ["border-color: var(--deco-sapphire)", "box-shadow: 0 0 12px 3px rgba(90,121,200,.35)"],
                                         "icon": ["color: #AFC2F0"]}},
        ],
    },

    # ------------------------------------------------------------ floor plan light pool (fades with the lamp)
    "deco_glow": {
        "card_mod": PLAIN,
        # picture-elements children don't get card-mod classes, so opt out of the theme's glass + brackets here
        "extra_styles": "ha-card::after, ha-card::before { display: none !important; }",
        "show_icon": False, "show_name": False, "show_state": False,
        "tap_action": {"action": "none"}, "hold_action": {"action": "none"},
        "styles": {
            "card": ["background: none", "border: none", "box-shadow: none", "padding: 0", "border-radius: 0",
                     "-webkit-backdrop-filter: none", "backdrop-filter: none", "width: 100%", "height: 100%",
                     "background-image: [[[ return `url(${variables.img})`; ]]]",
                     "background-size: 100% 100%", "background-repeat: no-repeat",
                     "opacity: [[[ if (!entity || entity.state !== 'on') return 0; const b = entity.attributes.brightness; return b ? (0.35 + 0.65 * b / 255).toFixed(2) : 1; ]]]",
                     "transition: opacity 1.2s ease"],
        },
    },

    # ------------------------------------------------------------ theme switch (Noir <-> Lite)
    "deco_theme_toggle": {
        "show_state": False,
        "icon": "mdi:palette-swatch-outline",
        "tap_action": {"action": "perform-action", "perform_action": "input_select.select_next",
                       "target": {"entity_id": "input_select.dashboard_theme"}},
        "hold_action": {"action": "more-info"},
        "name": "[[[ const lite = entity && entity.state === 'deco_noir_lite'; return `Theme · <b>${lite ? 'Deco Noir Lite' : 'Deco Noir'}</b> <span style='opacity:.55'>— tap for ${lite ? 'Noir' : 'Lite'}</span>`; ]]]",
        "styles": {
            "card": ["padding: 8px 14px", "height: 100%", "box-sizing: border-box"],
            "grid": ["grid-template-areas: '\"i n\"'", "grid-template-columns: 30px 1fr", "align-items: center", "column-gap: 10px"],
            "img_cell": ["width: 30px", "height: 30px"],
            "icon": ["width: 20px", "color: var(--deco-gold-hi)"],
            "name": ["justify-self: start", "font-family: var(--deco-label)", "font-size: 10px", "letter-spacing: .2em",
                     "text-transform: uppercase", "color: rgba(237,230,214,.7)", "white-space: nowrap", "overflow: hidden",
                     "text-overflow: ellipsis"],
        },
        "extra_styles": "b { color: var(--deco-gold-hi); font-weight: 600; }",
    },
}
