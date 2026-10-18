import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""跨视角一致性数值排查：① 人脸相似度（是否同一位模特）② 背景亮度/方差（是否同款背景）。"""
import os, json
import numpy as np
from PIL import Image

P = str(paths.BR + '/build' + '/panels')
OUT = str(paths.BR + '/qa' + '/consistency_report.json')
CODES = ["A1", "A2", "B1", "B2", "C1", "C2"]
VIEWS = ["front", "side", "three_quarter", "back", "bottom"]

# ---------- 背景指标 ----------
def bg_metrics(path):
    im = Image.open(path).convert("L"); im.thumbnail((500, 680))
    a = np.asarray(im, dtype=np.float32); H, W = a.shape
    band = np.concatenate([a[:int(H*0.25), :int(W*0.15)].ravel(),
                           a[:int(H*0.25), int(W*0.85):].ravel()])
    return float(band.mean()), float(band.std())

# ---------- 人脸相似度 ----------
faces = None
try:
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    faces = app
    print("insightface 就绪", flush=True)
except Exception as e:
    print("insightface 不可用:", type(e).__name__, str(e)[:120], flush=True)

def face_emb(path):
    if faces is None: return None
    img = np.asarray(Image.open(path).convert("RGB"))[:, :, ::-1]
    fs_ = faces.get(img)
    if not fs_: return None
    return max(fs_, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1])).normed_embedding

rep = {}
for code in CODES:
    rep[code] = {}
    base = None
    for v in VIEWS:
        p = os.path.join(P, "%s_%s.jpg" % (code, v))
        if not os.path.exists(p): continue
        m, sd = bg_metrics(p)
        e = face_emb(p)
        if v == "front":
            base = e
        cos = None
        if e is not None and base is not None:
            cos = float(np.dot(e, base))
        rep[code][v] = dict(bg_mean=round(m, 1), bg_std=round(sd, 1), face_cos=(round(cos, 3) if cos is not None else None),
                            has_face=e is not None)
        flag = ""
        if cos is not None and cos < 0.40: flag = "  <-- 模特可能不同"
        if e is None and v in ("front", "side", "three_quarter"): flag = "  <-- 未检出人脸"
        print("%s %-14s bg=%.0f/%.1f  face_cos=%s%s" % (code, v, m, sd, (("%.3f" % cos) if cos is not None else "—"), flag), flush=True)
json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1)
print("已写", os.path.basename(OUT))
