# Deco Noir

An Art Deco dashboard theme for Home Assistant: smoked-glass cards over a gold
sunburst, hairline double borders with stepped corner brackets, and 1920s typography.

Inspired by the dark glass look of [Tunet](https://github.com/oyvhov/Tunet) and the
room-banner structure of [Homio](https://github.com/iamtherufus/Homio), but built as a
native Home Assistant theme so it works in the companion app, the browser, and wall
tablets, and stays editable from the dashboard UI.

## Status

- **Phase 0: mockup.** Done. Open [`mockup/index.html`](mockup/index.html); chosen: champagne + Poiret One.
- **Phase 1: theme.** Applied to the `home-hub` dashboard (all views use `theme: deco_noir`).
- **Phase 2: cards.** button-card templates (`tools/deco_templates.py` → `templates/deco_templates.json`):
  `deco_lobby`, `deco_marquee`, `deco_room`, `deco_tile`, `deco_scene`, `deco_gauge`, `deco_rows`, `deco_marker`.
  New **Floor Plan** tab: `tools/make_floorplan.py` draws `www/deco/floor_{main,upper,lower}.svg`
  (Poiret One + Josefin Sans embedded, SIL OFL) and `tools/floor_markers.json`; markers glow when lamps are on.
  Rebuild/push with `HA_TOKEN_FILE=... python tools/build_dashboard.py`.

## Install

1. Install **card-mod** from HACS, and load it early in `configuration.yaml`:
   ```yaml
   frontend:
     extra_module_url:
       - /hacsfiles/lovelace-card-mod/card-mod.js
     themes: !include_dir_merge_named themes
   ```
2. Copy `themes/deco_noir.yaml` to `/config/themes/` and `www/deco/sunburst.svg` to `/config/www/deco/`.
3. Add a dashboard resource (type **CSS**):
   `https://fonts.googleapis.com/css2?family=Poiret+One&family=Josefin+Sans:wght@300;400;600&family=Jost:wght@200;300;400&display=swap`
4. Restart, then set `theme: deco_noir` on your views (or pick it in your profile).

Regenerate the background with `python tools/make_sunburst.py`.

## Design tokens

| Token | Champagne | Platinum | Use |
|---|---|---|---|
| `--ink` | `#0B0B0E` | same | page base |
| `--midnight` | `#11131C` | same | page gradient |
| `--ivory` | `#EDE6D6` | same | primary text |
| `--gold` | `#C9A44C` | `#A7AFBA` | lines, icons, frames |
| `--gold-hi` | `#E6CF9A` | `#E4E8EE` | accents, active text |
| `--glass` | `rgba(14,14,20,.55)` + `blur(18px)` | same | card surface |
| `--emerald` | `#3E9C82` | same | Yard / OK states |
| `--sapphire` | `#5A79C8` | same | Media |
| `--garnet` | `#B4404F` | same | alerts |

**Type:** Poiret One or Limelight (display), Josefin Sans (labels, spaced small caps),
Jost (numbers). **Icons:** Material Symbols Outlined at weight 200.

**Ornaments:** gold double hairline frame, stepped corner brackets, marquee section
headings (rule, ◆ title ◆, rule), diamond icon wells, and a soft gold halo on "on" states.

## Plan

1. **Phase 0: mockup.** Done.
2. **Phase 1: theme.** Done. `themes/deco_noir.yaml` (colors, state colors, fonts) plus a
   `card-mod-theme` for glass, frames, and headings. Fonts are loaded as a dashboard
   resource and the sunburst background lives in `www/deco/`. Requires
   [card-mod](https://github.com/thomasloven/lovelace-card-mod) (HACS).
3. **Phase 2: cards.** Done. [button-card](https://github.com/custom-cards/button-card)
   templates for the lobby clock, room banners, Deco tiles, gauges, and printer, with
   optional [Bubble Card](https://github.com/Clooos/Bubble-Card) room pop-ups.
4. **Phase 3: polish.** Phone layout, a no-blur "Lite" variant for low-power tablets,
   a WCAG contrast pass, and optional kiosk mode.

Only HACS-maintained dependencies; no hand-installed forks.

## Layout

```
mockup/        static HTML mockup (Phase 0)
themes/        Home Assistant theme YAML (Phase 1)
www/deco/      background art, fonts CSS (Phase 1)
templates/     button-card templates (Phase 2)
dashboards/    dashboard config exports (Phase 2)
```

## License

MIT
