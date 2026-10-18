# 04 · 3D garment method (optional branch)

Used when geometry must be provably correct (low-angle views, flat-lay
pattern shapes, ghost-mannequin product shots).

## Body
- Anny parametric human body (Apache-2.0, MakeHuman topology, 13.7k verts).
- Arms-down pose solved by grid search over upper-arm local X/Z angles:
  objective = the global max |x| vertex lands at hip height
  (|x|≈0.22, z≈0.70), with left/right symmetry; best found
  dx=-30°, dz=80° with the mirror rule "same X angle both sides, flip Z".
- Export via obj → import with up_axis='Z' (Blender's default Y-up import
  silently rotates the body 90° into the floor).

## Garment shells
- Parametric ray-casting from the body axis: z_lo(θ)/z_hi(θ) define the
  neckline and leg openings; offset pushes the shell off the skin.
- r_max must exceed the hip radius or the sides are dropped (a "bib").
- Drop connected components < 80 faces (ray-cast debris).
- `garments.py` holds all six style builders; `garments_all_metrics.json`
  is the geometric self-check (area, z-range, x-range, L/R asymmetry).

## Flattening (flat-lay)
- Unroll the shell by surface arc-length per row (x = arc, y = height):
  this is a real pattern shape, not a photo edit.
- Split front/back panels at the side seams and lay them side by side.

## Colour pitfalls in Blender
- AgX view transform lifts dark colours: switch to Standard.
- Strong speculars wash the fabric: roughness ~0.9 / specular 0.12 for
  matte swim fabric.
