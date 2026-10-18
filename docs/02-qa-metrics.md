# 02 · QA metrics

Each check is a standalone script in `qa/`; all were tuned against a real
6-style booklet.

| # | Check | Script | Criterion used |
|---|---|---|---|
| 1 | Effective resolution | qa_dpi.py | panels ≥373 dpi @72mm; details ≥313 dpi @64.25mm; none <300 |
| 2 | Competition/track hard rules | qa_compliance.py | page count, page size, single PDF ≤100MB, text layer, RGB |
| 3 | Cross-view identity | qa_consistency.py | insightface cosine vs the front view; note: profile views naturally score lower — always confirm visually |
| 4 | Bottom panel provenance | qa_bottom_recheck.py | re-crop from the current front, compare pixelwise; correlation must be 1.0000 (any staleness is auto-replaced) |
| 5 | Colour drift | qa_color_region2.py | figure-masked, per-spec-colour ΔE (CIE76); single-colour garments ≤15; multi-colour styles judged per region |
| 6 | Content safety | qa_modesty.py | torso-band skin ratio vs garment ratio; failing outputs deleted |
| 7 | Spec ↔ page text | qa_spec_match.py | every colour hex, key dim, claim, name must appear on the page |
| 8 | Layout structure | qa_layout.py | 5 panels, 4 detail crops, 4 tables, 5 view labels per page; no placeholder strings |
| 9 | Per-page JPG sync | qa_jpg_sync2.py | exported JPGs vs page PNGs, correlation ≥0.999 |

## Interpretation notes

- ΔE on a lit, glossy garment will exceed the flat spec value; judge
  *consistency across views*, not the absolute number.
- Template matching for "is this crop from that image" is fragile; prefer
  deterministic re-derivation + pixel compare (check 4).
- After any rebuild, re-apply PDF metadata and re-export JPGs — both are
  downstream artifacts that silently go stale.
