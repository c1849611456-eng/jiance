# 03 · Pitfalls (distilled from 30+ iteration rounds)

## Generative editing
- **Text cannot control camera angle.** Kontext and SDXL both ignored
  "45-degree" prompts across multiple seeds.
- **2D pose skeletons cannot encode body orientation** — a 45° view's
  keypoints project nearly frontally.
- **Depth ControlNet *can* encode orientation but sacrifices trailing
  garment parts** (robes, skirts, shorts collapse into one-pieces).
- **Kontext recomposes frames.** Always verify figure bbox drift; >4% is a
  reject. Two attempts passed design checks but changed framing.
- **"Remove the model" fails.** The model substitutes a mannequin and
  changes the design; same for dual-reference "make it a flat lay like
  image 2" — it copies the reference garment.

## Pipeline hygiene
- **Editing a view does not update its derived crops.** Re-derive the hem
  crop and the detail crops from the new source every time.
- **Layout reads `renders_v2/` before the raw folder.** Promoting a fix to
  the wrong directory silently changes nothing — check read priority.
- **cv2.imread/imwrite fail on non-ASCII paths** on Windows; use
  np.fromfile + imdecode / imencode + tofile.
- **4× upscale is easy to forget** for views that were regenerated from a
  896×1152 latent — one style shipped at 1/4 the resolution of the others.
- **PDF rebuilds drop metadata and stale the JPG exports.** Re-apply both.

## QA metric design
- Colour ΔE measured on the whole image is meaningless — the background
  contaminates it (brand-white backgrounds matched the white trim).
  Always mask the figure first, then measure per spec colour.
- "Lowest point of the arm" metrics get hijacked by the feet; use the
  location/height of the global max |x| instead.
- A near-white background is classified as "trim colour" at 80–92%
  coverage — background exclusion is mandatory.
