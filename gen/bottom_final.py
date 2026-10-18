import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""六款底视图最终生成：深度重投影(头部深度压平) + 经典背景清理（不用生成模型，发型/身份与正视一致）。"""
import os, sys
sys.path.insert(0, str(paths.BR + '/gen'))
import numpy as np
from PIL import Image, ImageFilter
import yaml
import depth_nvs
BR = str(paths.BR)
GEN = os.path.join(BR, "gen"); RAW = str(paths.RAW); R2 = os.path.join(BR, "renders_v2")
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
CODES = ["A1","A2","B1","B2","C1","C2"]

def front_of(c):
    for p in (os.path.join(R2, "%s_front.png" % c), os.path.join(RAW, "%s_front.png" % c)):
        if os.path.exists(p): return p
    return None

def mask_of(im, hexes, thr=60):
    a = np.asarray(im.convert("RGB"), dtype=np.float32); H, W, _ = a.shape
    ycc = np.asarray(im.convert("YCbCr"), dtype=np.float32)
    Y, Cb, Cr = ycc[:,:,0], ycc[:,:,1], ycc[:,:,2]
    m = (Cb>77)&(Cb<135)&(Cr>133)&(Cr<180)&(Y>40)
    for h in hexes:
        hh = h.lstrip("#")
        if max(int(hh[i:i+2],16) for i in (0,2,4)) > 205: continue
        t = np.array([int(hh[i:i+2],16) for i in (0,2,4)], dtype=np.float32)
        m |= np.sqrt(((a-t)**2).sum(axis=2)) < thr
    # 头发：低亮度、低饱和
    mx = a.max(axis=2); mn = a.min(axis=2)
    m |= (mx < 110) & ((mx - mn) < 42)
    mi = Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    m = np.asarray(mi) > 127
    cols = m.sum(axis=0)
    if cols.max() > 0:
        good = np.where(cols > 0.02*H)[0]
        if len(good) > 20:
            keep = np.zeros_like(m); keep[:, good[0]:good[-1]+1] = True; m &= keep
    return m

for c in CODES:
    src = front_of(c); dep = os.path.join(GEN, "%s_depth.png" % c)
    if not (src and os.path.exists(dep)):
        print("missing src/depth", c); continue
    nvs = os.path.join(GEN, "%s_nvs_flat.png" % c)
    if not os.path.exists(nvs):
        depth_nvs.render(src, dep, nvs, pitch=34.0, cam1_h=0.15)
    im = Image.open(nvs).convert("RGB").resize((896, 1152), Image.LANCZOS)
    W, H = im.size
    hexes = [x["hex"] for x in SPEC["styles"][CODES.index(c)]["colors"]]
    m = mask_of(im, hexes)
    md = Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(81))
    m2 = np.asarray(md) > 127
    soft = im.filter(ImageFilter.GaussianBlur(9))
    mf = Image.fromarray((m2*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    alpha = np.asarray(mf, dtype=np.float32)[:, :, None] / 255.0
    out = (np.asarray(im, dtype=np.float32)*alpha + np.asarray(soft, dtype=np.float32)*(1-alpha)).astype(np.uint8)
    Image.fromarray(out).filter(ImageFilter.GaussianBlur(0.35)).save(os.path.join(GEN, "%s_bottom_final.png" % c), quality=95)
    print("  %s bottom_final ok (mask %.3f)" % (c, float(m.mean())))
print("ALL DONE")
