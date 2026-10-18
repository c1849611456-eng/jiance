import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 4 轮：跨页色彩统一复核 —— 各款五格的主色 ΔE（实测 vs 规格）与背景色一致性。"""
import os
import numpy as np, cv2, yaml
BR = str(paths.BR)
P = os.path.join(BR, "build", "panels")
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
rd = lambda p: cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
def hex2bgr(h):
    h = h.lstrip("#"); return np.array([int(h[4:6],16), int(h[2:4],16), int(h[0:2],16)], dtype=np.float32)
def de(bgr, ref_hex):
    a = cv2.cvtColor(bgr.reshape(1,1,3).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
    b = cv2.cvtColor(hex2bgr(ref_hex).reshape(1,1,3).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
    return float(np.sqrt(((a-b)**2).sum()))
VIEWS = ["front", "side", "three_quarter", "back", "bottom"]
print("| 款 | 主色(规格) | " + " | ".join(VIEWS) + " | 背景亮度范围 |")
print("|---|---|" + "---|"*len(VIEWS) + "---|")
for st in SPEC["styles"]:
    c = st["code"]
    main = [x["hex"] for x in st["colors"] if x["role"] in ("主体", "底/渐变", "胸部")] or [st["colors"][0]["hex"]]
    main = main[0]
    des, bgs = [], []
    for v in VIEWS:
        p = os.path.join(P, "%s_%s.jpg" % (c, v))
        if not os.path.exists(p): des.append("—"); continue
        im = rd(p)
        h, w = im.shape[:2]
        # 主色像素：与该款主色距离 < 60 的像素取中位
        d = np.linalg.norm(im.astype(np.float32) - hex2bgr(main)[None, None, :], axis=2)
        m = d < 60
        col = np.median(im[m], axis=0) if m.sum() > 500 else np.median(im.reshape(-1,3), axis=0)
        des.append("%.1f" % de(col, main))
        # 背景：四角 8% 区域
        bg = np.concatenate([im[:int(h*0.08), :int(w*0.08)].reshape(-1,3), im[:int(h*0.08), int(w*0.92):].reshape(-1,3)])
        bgs.append(float(cv2.cvtColor(bg.reshape(-1,1,3).astype(np.uint8), cv2.COLOR_BGR2GRAY).mean()))
    print("| %s | %s | %s | %.0f–%.0f |" % (c, main, " | ".join(des), min(bgs) if bgs else 0, max(bgs) if bgs else 0))
