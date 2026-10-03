# v0.2 Task G report: README logo

- Branch: the v0.2 PR branch. This task committed nothing.
- Files this task owns: `docs/assets/**` and this report. No app, test, plan or ledger files were touched.

## Deliverables

| File | Size |
| --- | --- |
| `docs/assets/fontkit-logo-light.svg` | 5,518 B |
| `docs/assets/fontkit-logo-dark.svg` | 5,518 B |
| `docs/assets/README.md` | fonts, licences, `<picture>` snippet |
| `docs/assets/preview-light.png` | 14,961 B (logo on `#ffffff` at 420 px and 210 px) |
| `docs/assets/preview-dark.png` | 15,009 B (logo on `#0d1117` at 420 px and 210 px) |

Both SVGs:
- have a `viewBox` of `0 8 395 96` (395 × 96 units) and a transparent background;
- carry `role="img"` and `<title>fontkit</title>`;
- use only the elements `svg`, `title`, `mask`, `g`, `rect` and `path`;
- contain no `<text>`, `href`, external URL, script or raster image;
- round coordinates to 1 decimal place.

The generator scripts and downloaded font subsets stay in a scratch directory. None of them are in the repository.

## Fonts and licences

All five typefaces are under the SIL OFL 1.1. I confirmed this from each `ofl/<family>/OFL.txt` in `google/fonts` (HTTP 200). The font files were Google Fonts css2 subsets limited to the letters `fontkiO`.

| Letter(s) | Typeface |
| --- | --- |
| `f` | Source Serif 4 Bold, optical size 60 |
| `O` | Fraunces Black, optical size 144 |
| `n` | Courier Prime Bold |
| `t` | Inter Bold |
| `kit` | Crimson Pro Bold |

## Design decisions

- **Brief correction.** The `t` in "font" is a sans-serif. It is Inter Bold, and the spacing was redone around it. The `t` in "kit" stays Crimson Pro, in crimson.
- **Shared baseline and x-height.** Everything sits on one baseline at y = 84 with a shared x-height of 36 units. Each typeface was scaled to match that x-height. Crimson Pro is drawn at 106% so "kit" holds its own against the heavy `O` and `n`.
- **Hero O.** The Fraunces Black capital O is 68 units tall, about 1.9 times the x-height. It is drawn 92% as wide as it is tall, so it reads as a tall, heavy display O. Its strong contrast keeps it reading as a letter rather than a zero.
- **Rejected O candidates.** I also tried Playfair Display Black O, Fraunces SuperSoft Black, and a condensed lowercase o from Abril Fatface. They were close, but either read more like a zero or were too narrow.
- **The f.** I first tried a Fraunces 144pt f. At 50% scale its hairline crossbar and curled terminal stopped reading as an f. I tried Playfair, Source Serif 4 and Crimson Pro side by side and chose Source Serif 4 Bold, which is clean and sturdy.
- **The n.** Courier Prime Bold was chosen over JetBrains Mono, IBM Plex Mono and Space Mono. Its slab feet and typewriter shape read as monospace straight away, even at small size.
- **Spacing.** Gaps between letters were set by hand, measured between the inked edges of each glyph: f→O 2, O→n 3.5, n→t 3, k→i 1.5 and i→t 1.5 units. The gap between t and k is 6.5 units, so the two words separate by colour and spacing as well.
- **Artboard mark.** The mark is 58 × 58 units:
  - a rounded frame (3.5-unit stroke, roughly the weight of the letter stems);
  - print-style crop marks at all four corners (2.4-unit stroke so they survive 50% scale);
  - a tapered crimson wave of paint, drawn as a filled outline;
  - a paintbrush with crimson bristles at the end of the wave, a ferrule, and a handle leaving the frame to the upper right.
  An internal `<mask>` cuts a gap in the frame where the handle crosses it. The brush is the font colour with a crimson tip, which ties the mark to "kit". The space between the mark and the wordmark is about 12 units.
- **Colours.**
  - Light: "font" and the mark lines are `#1f2328` (GitHub's text colour); "kit" and the paint are exact crimson `#DC143C`.
  - Dark: "font" and the mark lines are `#f0f6fc`; "kit" is a slightly brighter crimson, `#E8264B`, because `#DC143C` looks muddy on dark.

## Contrast (WCAG 2.x)

| Element | Colour | Background | Ratio |
| --- | --- | --- | --- |
| "font" (light) | `#1f2328` | `#ffffff` | 15.80 : 1 |
| "kit" (light) | `#DC143C` | `#ffffff` | 4.99 : 1 |
| "font" (dark) | `#f0f6fc` | `#0d1117` | 17.39 : 1 |
| "kit" (dark) | `#E8264B` | `#0d1117` | 4.33 : 1 |

All four are at least 3:1; three of the four are also at least 4.5:1. The light file shown on a dark background (a viewer without `<picture>` support) would be unreadable for "font" (1.20:1). That is why the `<picture>` snippet with the dark source is required.

## Verification

1. I rendered candidate specimen sheets and full-logo variants with Python Playwright, using Chromium at `/opt/pw-browsers/chromium` (`--disable-gpu`). I did not run `playwright install`. I looked at each render and iterated through about six rounds: O choice, n and t choice, brush-mark shape, f replacement, spacing and size.
2. The final previews load each SVG through an `<img>` element from a data URI, the way GitHub serves README SVGs. Each is shown at `width=420` (1×) and `width=210` (0.5×) on its GitHub background. These are `docs/assets/preview-{light,dark}.png`.
3. I also checked a 3× device-scale render (scratch only). At both sizes the word reads "fontkit", the tall O is the focal point, the Courier n reads as monospace, the Inter t as sans-serif, and "kit" as crimson. The mask gap, crop marks and brush are crisp.
4. Both SVGs parse with `xml.etree`. I checked the element list and attributes and confirmed there is no `<text>`, external reference or script.

## Deviations

None from the brief. The one change is a correction: a sans-serif `t` in "font", noted above.
