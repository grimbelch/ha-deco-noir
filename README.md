# Deco Noir

## Optional Cogitator theme

**Cogitator** is the fourth selector option, based on the approved A1 / Pattern IX
mockup. Its Home layout uses the existing HA entities, numbered ENABLED/STANDBY
keys, scene commands, climate controls, printer status, and a large green-tinted
Spotify artwork panel. The status rail counts real room relays rather than
displaying invented CPU readings. All other Home sections and views are retained.

`www/cogitator/cogitator-card.js` extends the existing card's service/media helpers
and supplies its own layout and CSS. Scanlines, selective text/control glow, a
slow scan band, and local Cogitator fonts supply the phosphor treatment. The
**PHOSPHOR** button reduces effects per browser; OS reduced-motion preferences
disable the scan animation. Phone layouts stack the panels and omit the rail.

Assets/fonts come from the user's Cogitator repo; font licenses are included.
Deploy with `tools/deploy_seasons_assets.py --cogitator`, then
`tools/install_seasons.py --select-cogitator` (requires `HA_TOKEN_FILE`). The latter
backs up the dashboard, helper, automation, selection, and resources before saving.
Without the selection flag it preserves the current choice. The regular builder
includes all four themes. Refresh browser tabs after updating module resources.

## Optional Les Saisons theme

The Home view now has a **Theme** selector with **Deco Noir**, **Deco Noir Lite**,
and **Les Saisons**. Les Saisons uses an ivory and terracotta palette, with four
Mucha-inspired seasonal portraits framing live room controls. The original Deco
Home layout is retained and returns when either Deco option is selected.

The selection applies to all clients using Home Assistant's default theme. A
profile-level theme override takes precedence. The helper restores its choice
after restart, and `dashboard_theme_apply` applies it in light and dark modes.

Implementation: `themes/les_saisons.yaml`, `tools/seasons_dashboard.py`, and
`www/seasons/seasons-card.js` and `www/seasons/portraits.png`. The regular dashboard
builder includes Seasons. Revision 3 uses `www/seasons/headers-v3.png`, a 2-by-2
atlas of complete landscape headers (no portrait cropping), with large seasonal
bouquets surrounding the live titles. Generation details are in `headers-v3.json`.
Device switches, scene buttons, and media sliders share a consistent custom
control treatment; entity detail dialogs remain available by clicking the labels.
The custom card keeps the four rooms in continuous
illustrated frames, with a compact Scenes/Music/Climate row, live media controls,
printer status, and responsive four/two/one-column layouts.
Cormorant Garamond Italic is hosted locally as
`www/seasons/display.ttf` under its accompanying SIL Open Font License.
`tools/install_seasons.py` backs up the live dashboard/helper/automation under
`build/before-seasons-*`, adds the new option, and preserves the selected theme.
It reads the existing user API token from `HA_TOKEN_FILE` without printing it.
Run `tools/deploy_seasons_assets.py` to copy the theme, card, font, and artwork to
matching paths under `/config` before running it. The installer registers the
versioned JavaScript module resource and backs up the previous resource list.
Refresh existing browser tabs after deployment so they load the module.
`tools/check_seasons.py` verifies all three selections and restores the original
selection without operating household devices.

Artwork is generated with built-in Imagegen; it contains no controls or text.
The production UI uses actual HA entities rather than the illustrative values
in the design mockups. Original design studies are under `design/art-nouveau/`.

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
- **Phase 3: polish.** WCAG contrast pass (all body text ≥ 4.5:1), `deco_noir_lite` theme (no backdrop blur,
  for low-power tablets), phone-friendly floor markers, Deco tiles on every tab, and **light pools**: each lamp
  has a glow layer clipped to its room (`www/deco/glow_*.svg`) that fades in over 1.2s with `mix-blend-mode: screen`,
  scaled by dimmer brightness (`deco_glow` template).

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
4. **Phase 3: polish.** Done. Phone layout, a no-blur "Lite" variant for low-power tablets,
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
