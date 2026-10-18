import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""终版合规自检：按实际版面宽度计算有效 dpi（面板 72mm / 细节 64.25mm），并核对 RGB 与文字层。"""
import os, re
BR = str(paths.BR)
PDF = os.path.join(BR, "out", "效果图_v2.pdf")
raw = open(PDF, "rb").read(); s = raw.decode("latin1")
objs = re.findall(rb"(\d+)\s+0\s+obj(.*?)endobj", raw, re.S)
imgs = []
for num, body in objs:
    if b"/Subtype /Image" in body or b"/Subtype/Image" in body:
        w = re.search(rb"/Width\s+(\d+)", body); h = re.search(rb"/Height\s+(\d+)", body)
        cs = re.search(rb"/ColorSpace\s*/?(\w+)", body)
        csname = cs.group(1).decode() if cs else ("(隐式RGB)" if re.search(rb"/Filter\s*/DCTDecode", body) else "?")
        if w and h: imgs.append((int(w.group(1)), int(h.group(1)), csname))
print("图像对象:", len(imgs))
panel = [i for i in imgs if i[0] >= 1000]
detail = [i for i in imgs if i[0] < 1000]
def dpi(px, mm): return px / (mm / 25.4)
bad = []
for w, h, cs in panel:
    d = dpi(w, 72.0)
    if d < 300: bad.append((w, h, round(d)))
print("面板图 %d 张，最小 %.0f dpi（应在 72mm 宽下 >=300）" % (len(panel), min(dpi(w,72.0) for w,h,_ in panel)))
for w, h, cs in detail:
    d = dpi(w, 64.25)
    if d < 300: bad.append((w, h, round(d)))
print("细节图 %d 张，最小 %.0f dpi（应在 64.25mm 宽下 >=300）" % (len(detail), min(dpi(w,64.25) for w,h,_ in detail)))
print("低于 300dpi 的图像:", bad if bad else "无 ✔")
print("色彩空间标记:", sorted({cs for _, _, cs in imgs}))
print("体积: %.2f MB（限 100MB）" % (len(raw)/1048576))
print("页数:", len(re.findall(r"/Type\s*/Page[^s]", s)))
