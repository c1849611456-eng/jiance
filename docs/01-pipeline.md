# 01 · Pipeline

Six stages from brand colour to print-ready PDF.

## ① Brand colour quantification
- Extract the logo's alpha channel; sample only solid pixels (alpha > 0.98) to
  avoid anti-aliased edge pollution.
- Fit the gradient plane with least squares to confirm hue lock, then extend
  into the shared colourway.

## ② Single-source spec
- `spec/styles.yaml` drives every page string: names, colourways, key dims,
  materials, claims, standards, detail-crop boxes, view manifests.
- Changing the spec and re-running the build regenerates the booklet.

## ③ Visualization
- SDXL + IPAdapter (appearance reference = the style's own front view),
  one fixed seed per style across its four views.
- Prompt is frozen as: colour values + construction + fabric + pattern +
  view + lighting + finish details + negative list.

## ④ Targeted edits
- FLUX Kontext, single- or dual-reference (`kx.run` / `kx.run2`).
- Before promoting any edit: composition check (figure bbox drift ≤ 4%),
  coverage check (garment coverage in key bands), and modesty gate
  (skin ratio in torso band) — failing outputs are auto-deleted.

## ⑤ Technical calibration & QA
- Generative images are visual only; pattern dimensions come from the
  technical flats.
- QA harness: see docs/02-qa-metrics.md.

## ⑥ Typesetting
- Panels normalized to 1100×1467 (3:4), placed at 72 mm on A3 → ≥373 dpi.
- Detail crops upscaled 3× (≥313 dpi at 64.25 mm).
- HTML/CSS → Chrome headless `--print-to-pdf --no-pdf-header-footer`.
- Export never downscales pixels; images embedded as high-quality JPEG.
