import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""底视图改为「下摆（腿口/裆部）低位特写」：直接取自该款真实渲染的髋部到脚段，
不做任何几何变形 -> 比例与正视完全一致，也不会有重投影产生的白色拉伸线。"""
import os
import numpy as np
from PIL import Image, ImageFilter
BR = str(paths.BR)
GEN = os.path.join(BR, "gen"); RAW = str(paths.RAW); R2 = os.path.join(BR, "renders_v2")
CODES = ["A1","A2","B1","B2","C1","C2"]
TW, TH = 1100, 1467
ASPECT = TW / float(TH)

def src_of(c):
    for p in (os.path.join(R2, "%s_front.png" % c), os.path.join(RAW, "%s_front.png" % c)):
        if os.path.exists(p): return p

def subject_span(im):
    """用肤色快速定位人物竖直范围（正视图是全身像，结果稳定）。"""
    ycc = np.asarray(im.convert("YCbCr"), dtype=np.float32)
    Y, Cb, Cr = ycc[:,:,0], ycc[:,:,1], ycc[:,:,2]
    m = (Cb>77)&(Cb<135)&(Cr>133)&(Cr<180)&(Y>40)
    ys = np.where(m.sum(axis=1) > 0.004*im.size[0])[0]
    xs = np.where(m.sum(axis=0) > 0.004*im.size[1])[0]
    if len(ys) < 20: return None
    return int(ys[0]), int(ys[-1]), int((xs[0]+xs[-1])/2) if len(xs) else im.size[0]//2

for c in CODES:
    p = src_of(c)
    if not p: print("no src", c); continue
    im = Image.open(p).convert("RGB")
    W, H = im.size
    sp = subject_span(im)
    if not sp: print("span fail", c); continue
    top, bot, cx = sp
    fh = bot - top
    y0 = int(top + 0.37 * fh)          # 自腰部起（含下装主体）
    y1 = int(min(H, bot + 0.02 * fh))  # 脚底略下
    ch = y1 - y0
    cw = int(ch * ASPECT)
    if cw > W: cw = W; ch = int(cw / ASPECT); y0 = max(0, y1 - ch)
    x0 = int(max(0, min(cx - cw/2, W - cw)))
    crop = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((TW, TH), Image.LANCZOS)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
    crop.save(os.path.join(GEN, "%s_bottom_hem.png" % c), quality=95)
    print("%s: hem crop y[%d..%d] x[%d..%d] (人物 %d..%d)" % (c, y0, y1, x0, x0+cw, top, bot))
print("DONE")
