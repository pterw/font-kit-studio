# fontkit logo assets

| File | Use |
| --- | --- |
| `fontkit-logo-light.svg` | GitHub light theme: "font" in `#1f2328`, "kit" in crimson `#DC143C` |
| `fontkit-logo-dark.svg` | GitHub dark theme: "font" in `#f0f6fc`, "kit" in crimson `#E8264B` |
| `preview-light.png`, `preview-dark.png` | Chromium renders of each logo at 420 px and 210 px on `#ffffff` / `#0d1117` |

Both SVGs have transparent backgrounds, a `viewBox` of `0 8 395 96`, `role="img"` and `<title>fontkit</title>`.
Every glyph is an outlined `<path>`. The files contain no `<text>`, web fonts, scripts, raster images or external references, so GitHub's `<img>` rendering shows them exactly as designed.

## README snippet

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/fontkit-logo-dark.svg">
  <img alt="fontkit" src="docs/assets/fontkit-logo-light.svg" width="420">
</picture>
```

## Typefaces

Each letter was converted to outlines with fontTools, then placed and kerned by hand on a shared baseline. The two words share one x-height (36 units). The only exception is the hero O, which is 68 units tall.

| Letter(s) | Typeface | Licence | Source |
| --- | --- | --- | --- |
| `f` (serif) | Source Serif 4 Bold, optical size 60 | SIL Open Font License 1.1 | <https://github.com/google/fonts/tree/main/ofl/sourceserif4> (Adobe, `adobe-fonts/source-serif`) |
| `O` (big, bold, tall) | Fraunces Black, optical size 144, drawn 92% as wide as it is tall | SIL Open Font License 1.1 | <https://github.com/google/fonts/tree/main/ofl/fraunces> (`undercasetype/Fraunces`) |
| `n` (monospace) | Courier Prime Bold | SIL Open Font License 1.1 | <https://github.com/google/fonts/tree/main/ofl/courierprime> (`quoteunquoteapps/CourierPrime`) |
| `t` (sans-serif) | Inter Bold | SIL Open Font License 1.1 | <https://github.com/google/fonts/tree/main/ofl/inter> (`rsms/inter`) |
| `kit` (crimson serif) | Crimson Pro Bold, at 106% of the shared x-height | SIL Open Font License 1.1 | <https://github.com/google/fonts/tree/main/ofl/crimsonpro> (`Fonthausen/CrimsonPro`) |

The OFL allows using a font's glyphs in artwork such as a logo. The repository contains only the outlined shapes, not any font files.

The artboard mark is drawn by hand from basic SVG shapes and paths. It has a rounded frame with crop marks, a crimson brush stroke and a paintbrush. A mask leaves a small gap where the brush handle crosses the frame.
