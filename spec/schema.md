# styles.yaml schema

Single source of truth for the whole booklet. Every string on the rendered
pages (tables, captions, swatches) is generated from this file.

```yaml
brand: "Example Brand"          # shown in page footers
series: "EXAMPLE SERIES"
version: "v1.0"
standards_base:                 # shared per-page standards block
  - {item: "Colour fastness", value: "≥ 4", basis: "ISO 105-C06"}
styles:                          # one entry per style
  - code: A1                     # used for file naming {code}_{view}.png
    name_cn: 示例一
    name_en: EXAMPLE ONE
    series: "SEA A"
    scene: "Training / open water"
    seed: 100001                 # stable across the 4 views
    colors:                      # ordered; role drives the swatch caption
      - {name: Main, hex: "#1B3B8F", role: 主体, pct: 70}
    key_dims:                    # rendered in the dimension table
      - [Zip length, "40 cm"]
    materials:
      - [Shell, "Recycled nylon 72/28", "210 g/m²"]
    claims:
      - [UV protection, "UPF > 50", "GB/T 18830"]
    details:                     # close-up crops, normalized box [x0,y0,x1,y1]
      - {label: Collar & zip, view: front, box: [0.38, 0.17, 0.62, 0.36]}
    render_manifest:             # per-view source files
      front: A1_front.png
      side: A1_side.png
      back: A1_back.png
      three_quarter: A1_three_quarter.png
      bottom: A1_bottom.png
```

Notes:

- `code` must be unique and match the source image file names.
- `colors[].role` is free text; the layout renders it as-is.
- `details[].box` is normalized to the panel; `build/details.py` crops at 3×.
- All paths in the code are resolved from `paths.py`.
