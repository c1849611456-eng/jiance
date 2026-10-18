import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""细节特写：从归一化面板裁切并按 3× 输出（保证在 64mm 版面宽下 >=300dpi），JPEG 高质量。"""
import os
from PIL import Image
import yaml
BR = str(paths.BR)
OUT = os.path.join(BR, "build", "panels")
DETAIL = os.path.join(BR, "build", "details")
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
os.makedirs(DETAIL, exist_ok=True)
SCALE = 3
n = 0
for st in SPEC["styles"]:
    for i, d in enumerate(st.get("details", []), 1):
        p = os.path.join(OUT, "%s_%s.jpg" % (st["code"], d["view"]))
        if not os.path.exists(p):
            print("  skip", st["code"], d["view"]); continue
        im = Image.open(p); W, H = im.size
        x0, y0, x1, y1 = d["box"]
        crop = im.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H)))
        crop = crop.resize((crop.width*SCALE, crop.height*SCALE), Image.LANCZOS)
        crop.save(os.path.join(DETAIL, "%s_d%d.jpg" % (st["code"], i)), quality=95, subsampling=0)
        n += 1
print("details:", n, "（3x）")
