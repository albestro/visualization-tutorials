# slidev-theme-cscs

A Slidev theme matching the CSCS PowerPoint template (`CSCS_PowerPoint_template_16to9.pptx`).

## Features

- Light corporate theme with white background
- Arial system font stack
- CSCS color palette
- Global footer with slide number and logo placeholders
- Background images for cover/closing slides extracted from the PPTX
- Compatible layouts: `cover`, `section`, `default`, `statement`, `fact`, `quote`, `intro`, `author`, `image-left`, `image-right`

## Logos

The theme uses different CSCS logos for cover/section slides and content slides, matching the original PowerPoint template:

- `slidev-theme-cscs/public/cscs-logo.png` — cover / section header logo
- `slidev-theme-cscs/public/cscs-logo-short.png` — footer logo for default content slides
- `slidev-theme-cscs/public/eth-logo.png` — ETH logo (header + footer)

## Footer

Set the global footer text in `slides.md`:

```yaml
---
theme: cscs
defaults:
  footer: ParaView Users' Day 2026 | CSCS
---
```

## Backgrounds

The original PPTX template contains three cover-style background bands and one closing background. All are bundled in `slidev-theme-cscs/public/`:

| File | Use |
|------|-----|
| `/cover-bg.jpg` | Default `cover` layout background |
| `/cover-bg-alt1.jpg` | Alternative cover background (Title Slide 2) |
| `/cover-bg-alt2.jpg` | Alternative cover background (Title Slide 3) |
| `/closing-bg.jpg` | Closing / end slide background |

Swap them per slide in `slides.md`:

```yaml
---
layout: cover
background: /cover-bg-alt1.jpg
---
```

Or for an end slide:

```yaml
---
layout: cover
background: /closing-bg.jpg
---
```
