import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 6 轮（修正版）：先抠出人物（排除背景），再按规格分色统计 ΔE。"""
import os
import numpy as np, cv2, yaml
BR = str(paths.BR)
P = os.path.join(BR, "build", "panels")
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
rd = lambda p: cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
h2b = lambda h: np.array([int(h[5:7],16), int(h[3:5],16), int(h[1:3],16)], dtype=np.float32)
def lab(px):
    return cv2.cvtColor(np.array([[px]], dtype=np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
def de(px, hexs): return float(np.sqrt(((lab(px)-lab(h2b(hexs)))**2).sum()))
def figure_mask(im):
    h, w = im.shape[:2]
    edge = np.concatenate([im[:, :int(w*0.05)].reshape(-1,3), im[:, int(w*0.95):].reshape(-1,3)], axis=0)
    bg = np.median(edge, axis=0)
    d = np.linalg.norm(im.astype(np.float32) - bg[None,None,:], axis=2)
    m = (d > 42).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    n, lb, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        m = (lb == keep).astype(np.uint8)
    return m.astype(bool)
VIEWS = ["front", "side", "three_quarter", "back", "bottom"]
print("| 款 | 视角 | 人物占比 | 分色 ΔE（覆盖率） | 判定 |")
print("|---|---|---|---|---|")
for st in SPEC["styles"]:
    c = st["code"]; cols = [(x["hex"], x["role"]) for x in st["colors"]]
    for v in VIEWS:
        p = os.path.join(P, "%s_%s.jpg" % (c, v))
        if not os.path.exists(p): continue
        im = rd(p); fm = figure_mask(im)
        fg = im[fm]
        items = []
        for hx, role in cols:
            d = np.linalg.norm(fg.astype(np.float32) - h2b(hx)[None,:], axis=1)
            m = d < 55; cov = m.mean() if len(fg) else 0
            med = np.median(fg[m], axis=0) if m.sum() > 300 else None
            items.append((cov, role, (de(med, hx) if med is not None else None)))
        items.sort(reverse=True)
        dom = items[0]
        det = " ".join("%s %.0f(%.0f%%)" % (r, d if d is not None else -1, cv*100) for cv, r, d in items[:3] if cv > 0.02)
        verdict = "✅" if (dom[2] is None or dom[2] <= 15) else ("⚠️" if dom[2] <= 22 else "❌")
        print("| %s | %s | %.0f%% | %s | %s %s |" % (c, v, fm.mean()*100, det, verdict, ("ΔE=%.1f" % dom[2]) if dom[2] is not None else ""))
