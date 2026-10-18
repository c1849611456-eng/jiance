import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""定点修图（双参考 Kontext）：① C2 背视图改为真正的背影；② A1 45° 补上正视同款白色斜向胶条。"""
import os, sys, time
sys.path.insert(0, str(paths.BR + '/gen'))
import kx, pad
R2 = str(paths.R2)
PAD = os.path.join(str(paths.BR + '/gen'), "_padded"); os.makedirs(PAD, exist_ok=True)
FIX = os.path.join(str(paths.BR + '/gen'), "fix"); os.makedirs(FIX, exist_ok=True)

JOBS = [
    # (输出名, 待修图, 参考图, 指令)
    # C2 已完成
    ("C2_back_fix.png", "C2_back.png", "C2_front.png",
     "Turn this woman around so that we see her from directly BEHIND: a REAR view. We must see the back of her head with "
     "her hair bun, her bare back, the back of the bikini top with its horizontal back band and the back of the briefs. "
     "Her face must NOT be visible. Keep exactly the same woman, the same bikini design and colours (deep navy with teal "
     "band, seen in the second image), the same body proportions, the same studio background and the same lighting and "
     "framing. Photorealistic fashion photograph, no text"),
    ("A1_tq_fix.png", str(paths.RAW + '/A1_three_quarter.png'), "A1_front.png",
     "Add to this swimsuit the SAME single thin white bonded seam tape that runs diagonally across the chest in the second "
     "image, in exactly the same position and width, from the left shoulder area down towards the right waist. Keep "
     "everything else completely unchanged: the same woman, the same cobalt blue high-neck halter one-piece swimsuit, the "
     "same pose, the same background and lighting. Photorealistic, no text"),
]
for out, src, ref, instr in JOBS:
    outp = os.path.join(FIX, out)
    if os.path.exists(outp):
        print("skip", out, flush=True); continue
    p1 = os.path.join(PAD, "fix_%s" % src)
    pad.pad_image(os.path.join(R2, src) if not os.path.isabs(src) else src, p1, size=(896, 1152), fill=0.80)
    p2 = os.path.join(PAD, "fixref_%s" % ref)
    pad.pad_image(os.path.join(R2, ref), p2, size=(896, 1152), fill=0.80)
    kx.free_vram(); t = time.time()
    ok, note = kx.run2(p1, p2, instr, outp, seed=51000 + len(out), guidance=3.2)
    print(("OK " if ok else "FAIL ") + out + " " + str(note) + " %.0fs" % (time.time() - t), flush=True)
print("FIX DONE")
