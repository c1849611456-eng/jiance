import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""统一裁切 v2：同一款四视角共用同一缩放（按肤色高度中位数），位置各自对齐。"""
import os, json, statistics
import numpy as np
from PIL import Image
RAW = str(paths.RAW)
R2 = str(paths.R2)   # R2 新渲图优先

def resolve(fn):
    p2 = os.path.join(R2, fn)
    return p2 if os.path.exists(p2) else os.path.join(RAW, fn)
OUT = str(paths.BR + '/build' + '/panels')
QADIR = str(paths.BR + '/qa')
SPEC = str(paths.BR + '/spec' + '/styles.yaml')
os.makedirs(OUT, exist_ok=True); os.makedirs(QADIR, exist_ok=True)
import yaml
spec = yaml.safe_load(open(SPEC, encoding="utf-8"))
manifest = spec["render_manifest"]
TW, TH = 1100, 1467
ASPECT = TW / float(TH)
FIG_FILL = 0.90          # 人物高度占画面高度
SC = 8

def skin_info(im):
    small = im.resize((im.size[0]//SC, im.size[1]//SC), Image.BILINEAR)
    a = np.asarray(small.convert("YCbCr"), dtype=np.float32)
    Y, Cb, Cr = a[:,:,0], a[:,:,1], a[:,:,2]
    m = (Cb>77)&(Cb<135)&(Cr>133)&(Cr<180)&(Y>40)
    if m.sum() < 60: return None
    ys, xs = np.where(m)
    mid = m[int(m.shape[0]*0.20):int(m.shape[0]*0.80)]
    cs = mid.sum(axis=0).astype(np.float32)
    cxc = float((np.arange(m.shape[0]*0+mid.shape[1]) * cs).sum() / (cs.sum()+1e-6))
    return {"top": int(ys.min())*SC, "bot": (int(ys.max())+1)*SC, "cx": cxc*SC, "frac": float(m.mean())}

data = {}
for code, views in manifest.items():
    for v, fn in views.items():
        if not fn: continue
        im = Image.open(resolve(fn)).convert("RGB")
        info = skin_info(im)
        data[(code, v)] = {"im": im, "info": info, "fn": fn}
        print("%-3s %-14s src=%-34s skin=%s frac=%.3f" % (code, v, os.path.basename(resolve(fn)), "ok" if info else "MISS", info["frac"] if info else -1))

AS_IS_VIEWS = {"bottom"}   # 深度重投影输出本身已是 3:4、人物居中且占 88%，直接等比即可，避免肤色定位失败导致裁头

for code, views in manifest.items():
    keys = [(code, v) for v in views if views[v]]
    hs = [data[k]["info"]["bot"] - data[k]["info"]["top"] for k in keys if data[k]["info"]]
    if not hs: continue
    ref_h = statistics.median(hs)
    crop_h = ref_h / FIG_FILL
    crop_w = crop_h * ASPECT
    for k in keys:
        if k[1] in AS_IS_VIEWS:
            im = data[k]["im"]; W, H = im.size
            ch = float(H); cw = ch * ASPECT
            if cw > W: cw = float(W); ch = cw / ASPECT
            cx0 = int((W - cw) / 2); cy0 = int((H - ch) / 2)
            im.crop((cx0, cy0, cx0 + int(cw), cy0 + int(ch))).resize((TW, TH), Image.LANCZOS).save(
                os.path.join(OUT, "%s_%s.jpg" % k), quality=90, subsampling=0)
            print("  crop %-3s %-14s AS-IS (%.0fx%.0f -> 3:4)" % (k[0], k[1], cw, ch))
            continue
        im = data[k]["im"]; W, H = im.size; info = data[k]["info"]
        cw, ch = crop_w, crop_h
        if cw > W: cw = float(W); ch = cw / ASPECT
        if ch > H: ch = float(H); cw = ch * ASPECT
        if info is None or (info["bot"] - info["top"]) < 0.55 * ref_h:
            a = np.asarray(im.convert("RGB"), dtype=np.float32)
            m0 = max(8, int(0.03 * min(H, W)))
            bd = np.concatenate([a[:m0].reshape(-1,3), a[-m0:].reshape(-1,3), a[:, :m0].reshape(-1,3), a[:, -m0:].reshape(-1,3)])
            bgc = np.median(bd, axis=0)
            mk = np.sqrt(((a - bgc) ** 2).sum(axis=2)) > 26
            ys = np.where(mk.sum(axis=1) > 0.02 * W)[0]
            xs = np.where(mk.sum(axis=0) > 0.01 * H)[0]
            if len(ys) > 20 and len(xs) > 20:
                cx = float((xs[0] + xs[-1]) / 2.0); bot = int(ys[-1])
            else:
                cx = W/2.0; bot = int(0.95*H)
        else:
            cx = info["cx"]; bot = info["bot"]
        cx0 = int(round(cx - cw/2)); cy1 = int(round(bot + 0.05*ch)); cy0 = int(round(cy1 - ch))
        cx0 = max(0, min(cx0, int(W-cw))); cy0 = max(0, min(cy0, int(H-ch)))
        box = (cx0, cy0, cx0+int(cw), cy0+int(ch))
        data[k]["im"].crop(box).resize((TW, TH), Image.LANCZOS).save(os.path.join(OUT, "%s_%s.jpg" % k), quality=90, subsampling=0)
        print("  crop %-3s %-14s ref_h=%d crop_h=%d box=%s" % (k[0], k[1], ref_h, int(ch), str(box)))

tile = (300, 386)
sheet = Image.new("RGB", (tile[0]*4, tile[1]*len(manifest)), (250,250,250))
for i, code in enumerate(manifest.keys()):
    for j, v in enumerate(["front","side","three_quarter","back"]):
        p = os.path.join(OUT, "%s_%s.jpg" % (code, v))
        if os.path.exists(p): sheet.paste(Image.open(p).resize(tile), (j*tile[0], i*tile[1]))
sheet.save(os.path.join(QADIR, "panels_normalized.jpg"), quality=88)
print("sheet ok")


# ---- COLOR UNIFY：同款各视角的成衣/背景色向正视图对齐 ----
def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

def garment_mask(arr, hexes, tol=70):
    m = np.zeros(arr.shape[:2], dtype=bool)
    for h in hexes:
        c = hex2rgb(h)
        m |= np.sqrt(((arr - c) ** 2).sum(axis=2)) < tol
    return m

unify_log = []
for st in spec["styles"]:
    code = st["code"]
    hexes = [c["hex"] for c in st["colors"]]
    ref_path = os.path.join(OUT, "%s_front.jpg" % code)
    if not os.path.exists(ref_path):
        continue
    ref = np.asarray(Image.open(ref_path).convert("RGB"), dtype=np.float32)
    rmask = garment_mask(ref, hexes)
    if rmask.sum() < 500:
        print("  unify skip (no garment px)", code); continue
    rmean = ref[rmask].mean(axis=0)
    for v in list(manifest[code].keys()):
        if v == "front" or not manifest[code][v]:
            continue
        fp = os.path.join(OUT, "%s_%s.jpg" % (code, v))
        if not os.path.exists(fp):
            continue
        arr = np.asarray(Image.open(fp).convert("RGB"), dtype=np.float32)
        m = garment_mask(arr, hexes)
        if m.sum() < 300:
            continue
        tmean = arr[m].mean(axis=0)
        gain = np.clip(rmean / np.maximum(tmean, 1.0), 0.86, 1.16)
        out = np.clip(arr * gain, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(fp, quality=90, subsampling=0)
        unify_log.append((code, v, [round(float(x), 3) for x in gain]))
        print("  unify %-3s %-14s gain=%s" % (code, v, [round(float(x), 3) for x in gain]))
import json as _json
_json.dump(unify_log, open(os.path.join(OUT, "_color_unify.json"), "w"), ensure_ascii=False, indent=1)

# ---- 细节特写：从归一化面板上按相对坐标裁切并放大 ----
DETAIL = str(paths.BR + '/build' + '/details')
os.makedirs(DETAIL, exist_ok=True)
for st in spec["styles"]:
    for i, d in enumerate(st.get("details", []), 1):
        v = d["view"]
        p = os.path.join(OUT, "%s_%s.jpg" % (st["code"], v))
        if not os.path.exists(p):
            print("  detail skip (no view)", st["code"], v); continue
        im = Image.open(p)
        W, H = im.size
        x0, y0, x1, y1 = d["box"]
        box = (int(x0*W), int(y0*H), int(x1*W), int(y1*H))
        crop = im.crop(box)
        crop = crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
        crop.save(os.path.join(DETAIL, "%s_d%d.jpg" % (st["code"], i)), quality=90, subsampling=0)
        print("  detail %-3s d%d %-22s %s" % (st["code"], i, d["label"], str(box)))
