# AI This Week — the brand (founder decision 2026-11-16)

One look for everything the show puts out: videos, thumbnails, Shorts, the channel, LinkedIn.
The founder chose it after rejecting navy-and-gold with glows ("AI slop"), a cream-and-red editorial
look, four muted palettes and four gold-on-dark palettes. Do not drift back to any of those.

## Colours
| Token | Value | Use |
|---|---|---|
| Ground | `#2C0F66` royal violet | every background |
| Deep | `#1E0A47` | label plates over footage |
| White | `#FFFFFF` | all text unless it is gold |
| Gold | `#D9B13B` flat, or the foil gradient | the show's name ("AI"), the key figure, one accent word, thin rules |
| Quiet | `#B9A9DD` | small secondary text |

Gold is balanced, not everywhere: one gold element on a screen, the rest white.
The foil gradient is for that one element; thin lines use it too. Never a glow.

## Type
- **Sora** (800) for the name and headlines. Clean modern sans; the founder asked for this style.
- **Inter** for running text.
- **JetBrains Mono**, capitals with wide spacing, for sources, dates and small labels.

## Never
Glows, particles, circuit lines, gradient backgrounds, drop shadows, generated faces or figures,
a serif headline face, red, green, cream.

## Where it lives
`pipeline/post/visual_assets.py` holds the tokens; cards, overlays, thumbnail, end card and Shorts read
them. `sting/film.js` carries the same values. `scripts/brand_assets.py assets/brand` rebuilds the logo
and banners. Fonts are in `assets/fonts/` (all under the Open Font License).
