import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""实拍照片入库：自动裁成 3:4 面板 -> 按该款既有图做色彩匹配 -> 覆盖底视图 -> 重建页面。

用法：
  python photo_intake.py <照片目录>
照片命名：{CODE}_bottom.jpg（如 A1_bottom.jpg；也可 A1_bottom_01.jpg，取第一张）
可选：{CODE}_bottom_hem.jpg 作为「下摆特写」面板。

流程：EXIF 转正 -> 肤色定位人物 -> 3:4 裁切（人物高占 88%，脚底留 4%）
      -> 与 renders_v2/{CODE}_front.png 做均值/白平衡匹配 -> 写 renders_v2/{CODE}_bottom_low.png
      -> 记录到 render_provenance.json
之后执行：prep_panels.py -> brand_align.py -> details.py -> build_pages.py 即完成排版。
"""
import os, re, sys, json, hashlib, datetime
import numpy as np
from PIL import Image, ImageFilter, ImageOps

BR = str(paths.BR)
RAW = str(paths.RAW)
R2 = os.path.join(BR, "renders_v2")
GEN = os.path.join(BR, "gen")
QA = os.path.join(BR, "qa")
PROV = os.path.join(BR, "spec", "render_provenance.json")
TW, TH = 1100, 1467
ASPECT = TW / float(TH)
CODES = ["A1", "A2", "B1", "B2", "C1", "C2"]

def subject(im):
    ycc = np.asarray(im.convert("YCbCr"), dtype=np.float32)
    Y, Cb, Cr = ycc[:, :, 0], ycc[:, :, 1], ycc[:, :, 2]
    m = (Cb > 77) & (Cb < 135) & (Cr > 133) & (Cr < 180) & (Y > 40)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    m = np.asarray(mi) > 127
    W, H = im.size
    ys = np.where(m.sum(axis=1) > 0.004 * W)[0]
    xs = np.where(m.sum(axis=0) > 0.004 * H)[0]
    if len(ys) < 30 or len(xs) < 30:
        return None
    return int(xs[0]), int(ys[0]), int(xs[-1]), int(ys[-1])

def color_match(im, ref):
    """把 im 的成衣/整体色调整体拉向 ref（按中位数做通道增益，保留明暗）。"""
    a = np.asarray(im, dtype=np.float32); b = np.asarray(ref, dtype=np.float32)
    ma = np.median(a.reshape(-1, 3), axis=0); mb = np.median(b.reshape(-1, 3), axis=0)
    gain = np.clip(mb / np.maximum(ma, 1.0), 0.85, 1.18)
    return Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8))

def process_photo(path, code):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    W, H = im.size
    sp = subject(im)
    if sp is None:
        print("  %s: 未找到人物，跳过" % os.path.basename(path)); return None
    x0, y0, x1, y1 = sp
    fh = y1 - y0
    ch = fh / 0.88
    cw = ch * ASPECT
    if cw > W: cw = float(W); ch = cw / ASPECT
    if ch > H: ch = float(H); cw = ch * ASPECT
    cx = (x0 + x1) / 2.0
    cx0 = int(max(0, min(cx - cw / 2, W - cw)))
    cy1 = int(min(H, y1 + 0.045 * ch)); cy0 = int(max(0, cy1 - ch))
    crop = im.crop((cx0, cy0, cx0 + int(cw), cy0 + int(ch))).resize((TW, TH), Image.LANCZOS)
    ref_p = os.path.join(R2, "%s_front.png" % code) if os.path.exists(os.path.join(R2, "%s_front.png" % code)) else os.path.join(RAW, "%s_front.png" % code)
    if os.path.exists(ref_p):
        ref = Image.open(ref_p).convert("RGB").resize((TW, TH), Image.LANCZOS)
        crop = color_match(crop, ref)
    out = os.path.join(GEN, "%s_bottom_photo.png" % code)
    crop.save(out, quality=95)
    dst = os.path.join(R2, "%s_bottom_low.png" % code)
    crop.save(dst, quality=95)
    prov = json.load(open(PROV, encoding="utf-8")) if os.path.exists(PROV) else {}
    prov["%s_bottom_low" % code] = {"src": os.path.basename(path), "md5": hashlib.md5(open(dst, "rb").read()).hexdigest()[:12],
                                    "note": "实拍照片入库（自动 3:4 裁切 + 色彩匹配）",
                                    "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    json.dump(prov, open(PROV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %s: %s -> %s" % (code, os.path.basename(path), os.path.basename(dst)))
    return dst

def main(folder):
    files = os.listdir(folder)
    done = []
    for c in CODES:
        cands = sorted([f for f in files if re.match(r"^%s_bottom(_\d+)?\.(jpg|jpeg|png|tif|tiff)$" % c, f, re.I)])
        if not cands:
            continue
        done.append(process_photo(os.path.join(folder, cands[0]), c))
    print("入库完成：%d 款" % len(done))
    print("接着跑： prep_panels.py -> brand_align.py -> details.py -> build_pages.py")

if __name__ == "__main__":
    main(sys.argv[1])
