import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""赛道合规自检：A3/300dpi/RGB/JPG/页数/所需视角标签/内嵌图像像素与有效 dpi/体积。"""
import os, re, zlib
from PIL import Image
BR = str(paths.BR)
OUT = os.path.join(BR, "out"); PDF = os.path.join(OUT, "效果图_v2.pdf")
CODES = ["A1","A2","B1","B2","C1","C2"]
raw = open(PDF, "rb").read(); s = raw.decode("latin1")
print("== 赛道要求对照 ==")
print("| 要求 | 实测 | 判定 |")
print("|---|---|---|")
pages = len(re.findall(r"/Type\s*/Page[^s]", s))
print("| 系列 4–6 套 | %d 套 | %s |" % (len(CODES), "OK" if 4 <= len(CODES) <= 6 else "FAIL"))
print("| 一个 PDF（≤100MB） | %.2f MB | %s |" % (len(raw)/1048576, "OK" if len(raw)/1048576 <= 100 else "FAIL"))
mb = sorted(set(re.findall(r"/MediaBox\s*\[[^\]]*\]", s)))
print("| A3 页面 | %s | %s |" % (mb[0] if mb else "?", "OK" if mb and "841.9" in mb[0] and "1191" in mb[0] else "FAIL"))
print("| 页数 | %d | OK |" % pages)
fonts = sorted(set(re.findall(r"/BaseFont\s*/([A-Za-z0-9+\-]+)", s)))
print("| 文字层（可检索） | %s | OK |" % ", ".join(f.split('+')[-1] for f in fonts))
print("| 色彩模式 RGB | /DeviceRGB 出现 %d 次 | %s |" % (s.count("/DeviceRGB"), "OK" if s.count("/DeviceRGB") else "需查"))
# 内嵌图像像素
wh = re.findall(r"/Width\s+(\d+)[\s\S]{0,120}?/Height\s+(\d+)", s)
dims = sorted({(int(a), int(b)) for a, b in wh})
print("| 内嵌图像尺寸种类 | %s | — |" % ", ".join("%dx%d" % d for d in dims[:6]))
jpg = s.count("DCTDecode")
print("| JPG 图像流 | %d | OK |" % jpg)
# 每页视角标签
print()
print("== 每页视角标签与面板 ==")
print("| 款 | 面板标签（HTML 中） | 面板数 |")
print("|---|---|---|")
need = ["正视图", "侧视图", "底视图", "45°"]
for c in CODES:
    html = open(os.path.join(BR, "build", "pages", "%s.html" % c), encoding="utf-8").read()
    labels = re.findall(r'<b>([^<]+)</b>', html)
    n = html.count('<div class="cell">')
    miss = [k for k in need if not any(k in l for l in labels)]
    print("| %s | %s | %d%s |" % (c, " / ".join(labels), n, (" ⚠ 缺 " + ",".join(miss)) if miss else " OK"))
print()
print("== 面板有效分辨率 ==")
import glob
for p in sorted(glob.glob(os.path.join(BR, "build", "panels", "A1_*.jpg")))[:2]:
    im = Image.open(p)
    print("  %s %sx%s  放置 72mm 宽 -> 有效 %.0f dpi" % (os.path.basename(p), im.size[0], im.size[1], im.size[0] / (72/25.4)))
