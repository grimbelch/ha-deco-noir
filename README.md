# Deco Noir

An Art Deco dashboard theme for Home Assistant: smoked-glass cards over a gold
sunburst, hairline double borders with stepped corner brackets, and 1920s typography.

Inspired by the dark glass look of [Tunet](https://github.com/oyvhov/Tunet) and the
room-banner structure of [Homio](https://github.com/iamtherufus/Homio), but built as a
native Home Assistant theme so it works in the companion app, the browser, and wall
tablets, and stays editable from the dashboard UI.

## Status

**Phase 0: mockup.** Open [`mockup/index.html`](mockup/index.html) in a browser. The
buttons at the top switch the metal (champagne/platinum) and heading font
(Poiret One/Limelight).

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

1. **Phase 0: mockup.** Done. Iterate on look here first.
2. **Phase 1: theme.** `themes/deco_noir.yaml` (colors, state colors, fonts) plus a
   `card-mod-theme` for glass, frames, and headings. Fonts are loaded as a dashboard
   resource and the sunburst background lives in `www/deco/`. Requires
   [card-mod](https://github.com/thomasloven/lovelace-card-mod) (HACS).
3. **Phase 2: cards.** [button-card](https://github.com/custom-cards/button-card)
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
