import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""按款把成衣主色向品牌色归一（只作用于成衣区域，软掩膜，保留明暗）。"""
import os, json
import numpy as np
from PIL import Image
import yaml
BR = str(paths.BR)
PANELS = os.path.join(BR, "build", "panels")
spec = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
VIEWS = ["front", "side", "three_quarter", "bottom", "back"]

def h2rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

def lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = (M @ c) * 100 / np.array([95.047, 100.0, 108.883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])

log = []
for st in spec["styles"]:
    code = st["code"]
    main = max(st["colors"], key=lambda c: c["pct"])
    tgt = h2rgb(main["hex"])
    for v in VIEWS:
        p = os.path.join(PANELS, "%s_%s.jpg" % (code, v))
        if not os.path.exists(p):
            continue
        arr = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
        d = np.sqrt(((arr - tgt) ** 2).sum(axis=2))
        w = np.exp(-(np.clip(d - 25, 0, None) ** 2) / (2 * 55.0 ** 2))       # 成衣软掩膜
        w = w * (d < 120)
        if w.sum() < 200:
            continue
        dm = float(np.linalg.norm(lab(tgt) - lab(tgt)))
        cur = arr[w > 0.5]
        before = float(np.linalg.norm(lab(cur.mean(axis=0)) - lab(tgt))) if cur.size else -1
        gain = np.clip(tgt / np.maximum(cur.mean(axis=0), 1.0), 0.80, 1.25)
        strength = 0.85
        g = 1.0 + w[:, :, None] * (gain * strength + (1 - strength) - 1.0)
        out = np.clip(arr * g, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(p, quality=90, subsampling=0)
        arr2 = out.astype(np.float32)
        cur2 = arr2[w > 0.5]
        after = float(np.linalg.norm(lab(cur2.mean(axis=0)) - lab(tgt))) if cur2.size else -1
        log.append({"code": code, "view": v, "target": main["hex"], "dE_before": round(before, 1),
                    "dE_after": round(after, 1), "gain": [round(float(x), 3) for x in gain]})
        print("  align %-3s %-14s dE %.1f -> %.1f  gain=%s" % (code, v, before, after, [round(float(x),3) for x in gain]))
json.dump(log, open(os.path.join(PANELS, "_brand_align.json"), "w"), ensure_ascii=False, indent=1)
print("brand align done:", len(log), "views")
