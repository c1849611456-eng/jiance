import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 2 轮：技术图_Technical.pdf 合规与内容核对（页数/尺寸/图像/文字/款式覆盖）。"""
import os, re, io
from pypdf import PdfReader
from PIL import Image
PDF = str(paths.DELIVER + '/技术图_Technical.pdf')
OUT = str(paths.BR + '/qa' + '/tech')
os.makedirs(OUT, exist_ok=True)
print("体积: %.2f MB" % (os.path.getsize(PDF)/1048576))
r = PdfReader(PDF)
print("页数:", len(r.pages))
t_all = ""
for i, pg in enumerate(r.pages, 1):
    mb = pg.mediabox
    w, h = float(mb.width), float(mb.height)
    t = pg.extract_text() or ""
    t_all += t
    nimg = 0
    try: nimg = len(pg.images)
    except Exception: pass
    cn = len(re.findall(r"[\u4e00-\u9fff]", t))
    print("  第%d页: %.0f x %.0f pt (%.0f x %.0f mm)  文字 %d 字  图 %d 张" % (i, w, h, w/72*25.4, h/72*25.4, cn, nimg))
    for j, im in enumerate(pg.images, 1):
        img = Image.open(io.BytesIO(im.data))
        dst = os.path.join(OUT, "p%d_%d.png" % (i, j))
        img.save(dst)
        print("     图%d: %dx%d -> %s" % (j, img.size[0], img.size[1], dst))
print()
print("款式覆盖检查：")
for k in ["釉面", "蚀岸", "松线", "琥珀", "浅滩", "宝石", "A1", "A2", "B1", "B2", "C1", "C2"]:
    print("  %-4s %s" % (k, "✓" if k in t_all else "✗"))
