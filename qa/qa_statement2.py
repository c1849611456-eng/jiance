import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""抽取作品说明.pdf 的内嵌图片与页面尺寸，判断它是"图片版"还是"文字版"。"""
import os
from pypdf import PdfReader
from PIL import Image
import io
PDF = str(paths.DELIVER + '/作品说明.pdf')
OUT = str(paths.BR + '/qa' + '/statement')
os.makedirs(OUT, exist_ok=True)
r = PdfReader(PDF)
for i, p in enumerate(r.pages, 1):
    mb = p.mediabox
    print("第%d页 尺寸 %.1f x %.1f pt (%.0f x %.0f mm)" % (i, float(mb.width), float(mb.height),
          float(mb.width) / 72 * 25.4, float(mb.height) / 72 * 25.4))
    try:
        for j, im in enumerate(p.images, 1):
            data = im.data
            img = Image.open(io.BytesIO(data))
            dst = os.path.join(OUT, "p%d_%d.png" % (i, j))
            img.save(dst)
            print("   图%d: %sx%s %s -> %s" % (j, img.size[0], img.size[1], img.mode, dst))
    except Exception as e:
        print("   取图失败:", type(e).__name__, str(e)[:80])
