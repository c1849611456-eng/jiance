import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""继续修：B1 正视补白线 / B1 背视拉链改深蓝 / C1 45° 网点对齐正视（双参考 Kontext）。"""
import os, sys, time
sys.path.insert(0, str(paths.BR + '/gen'))
import kx, pad
RAW = str(paths.RAW)
R2 = str(paths.R2)
PAD = os.path.join(str(paths.BR + '/gen'), "_padded"); os.makedirs(PAD, exist_ok=True)
FIX = os.path.join(str(paths.BR + '/gen' + '/fix')); os.makedirs(FIX, exist_ok=True)

WHITE = ("Add the same clean white piping lines to this garment as in the second image: the thin brand-white (#E8E4DC) "
         "panelled seam lines running along the raglan shoulder and down the sleeve, exactly the same placement, width "
         "and colour. Keep everything else identical: same woman, same deep sage green long-sleeve one-piece swimsuit "
         "with knee sleeves, same pose, same background and lighting. Photorealistic, no text")
ZIP = ("Change the front zipper on this swimsuit so that it is dark navy blue (#1E4E65), matching the brand navy trim of "
       "the knee sleeves in the second image, instead of the current pale grey zip. Keep everything else identical: same "
       "woman seen from behind, same deep sage green swimsuit, same pose, background and lighting. Photorealistic, no text")
DOTS = ("Match the print of this swimsuit dress to the second image: the same white dotted engineered print on the teal "
        "mesh skirt with the same dot density and the same white gradient bodice with the same dotted density at the top. "
        "Keep everything else identical: same woman, same pose, same background and lighting. Photorealistic, no text")

JOBS = [
    ("B1_front_lines.png", os.path.join(R2, "B1_front.png"),    os.path.join(RAW, "B1_side.png"),       WHITE, 61001),
    ("B1_back_zip.png",    os.path.join(RAW, "B1_bottom.png"),  os.path.join(R2, "B1_front.png"),       ZIP,   61002),
    ("C1_tq_dots.png",     os.path.join(RAW, "C1_three_quarter.png"), os.path.join(R2, "C1_front.png"), DOTS,  61003),
]
for out, src, ref, instr, seed in JOBS:
    outp = os.path.join(FIX, out)
    if os.path.exists(outp): print("skip", out, flush=True); continue
    p1 = os.path.join(PAD, "fx_%s" % os.path.basename(src)); p2 = os.path.join(PAD, "fxr_%s" % os.path.basename(ref))
    pad.pad_image(src, p1, size=(896, 1152), fill=0.80)
    pad.pad_image(ref, p2, size=(896, 1152), fill=0.80)
    kx.free_vram(); t = time.time()
    ok, note = kx.run2(p1, p2, instr, outp, seed=seed, guidance=3.2)
    print(("OK " if ok else "FAIL ") + out + " " + str(note) + " %.0fs" % (time.time() - t), flush=True)
print("FIX2 DONE")
