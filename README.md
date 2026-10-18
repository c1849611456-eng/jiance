# Azure Stroke Pipeline

A production-style workflow for generating a multi-style apparel lookbook as
print-ready PDFs, with automated QA at every step.

**This is the method, not the product.** The repository contains the pipeline
code, the spec schema, and the QA harness. It does **not** contain model
weights, fonts, brand assets, or generated images — see [NOTICE.md](NOTICE.md).

## Pipeline overview

```
① brand colour quantification  (Python/NumPy)
② single-source spec           (spec/styles.yaml → every page string)
③ garment visualization        (SDXL + IPAdapter, same seed per style)
④ targeted edits               (FLUX Kontext: seams / models / lines)
⑤ technical calibration & QA   (Blender+Anny, insightface, RMBG, DPI, ΔE)
⑥ typesetting                  (HTML/CSS → Chrome headless → PDF)
```

## Layout

| dir | content |
|---|---|
| `spec/` | schema documentation + example data (fictional brand) |
| `gen/` | ComfyUI drivers (Kontext single/dual reference, SDXL batches, controlnets) |
| `build/` | panel normalization, colour alignment, detail crops, HTML→PDF, metadata |
| `qa/` | the QA harness (see docs/02-qa-metrics.md) |
| `threed/` | parametric garment shells on a CC0 body (Blender) |
| `docs/` | pipeline, metrics, pitfalls, 3D garment method |

## Quick start

1. Install ComfyUI (GPL-3.0) locally and download the checkpoints listed in
   [NOTICE.md](NOTICE.md); start it on `127.0.0.1:8188`.
2. `pip install -r requirements.txt` (pypdf, opencv-python, numpy, pillow, pyyaml, onnxruntime).
3. Copy `spec/example.yaml` to `spec/styles.yaml` and edit your styles.
4. `python gen/kx.py` (sanity check) → `python build/prep_panels.py` →
   `python build/build_pages.py` → run `python qa/qa_dpi.py` etc.
5. Read `docs/01-pipeline.md` for the full sequence and thresholds.

## Requirements

- Windows + Chrome (headless PDF export)
- Python 3.10+ with `opencv-python`, `numpy`, `Pillow`, `PyYAML`, `pypdf`
- ComfyUI 0.38 with the workflow extensions used by `gen/` (IPAdapter nodes,
  controlnet aux)
- Blender 4/5 with `bpy` for `threed/`

## License

Code: MIT. Third-party components: see NOTICE.md.
