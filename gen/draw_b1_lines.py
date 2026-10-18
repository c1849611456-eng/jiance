import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""在 B1 正视上确定性地画白色线条（体侧两道 + 胸下横线），不改变取景/比例。"""
import os
from PIL import Image, ImageDraw, ImageFilter
SRC = str(paths.R2 + '/B1_front.png')
DST = str(paths.BR + '/gen' + '/fix/B1_front_drawnlines.png')
im = Image.open(SRC).convert("RGB")
W, H = im.size
# 归一化坐标（基于 1100x1467 面板的实测构图）
P = lambda x, y: (x * W, y * H)
lines = [
    # 左体侧：腋下 -> 腰 -> 胯（按全身构图重新标定）
    [(0.448, 0.300), (0.436, 0.340), (0.432, 0.385), (0.436, 0.425), (0.452, 0.462), (0.470, 0.488)],
    # 右体侧
    [(0.552, 0.300), (0.564, 0.340), (0.568, 0.385), (0.564, 0.425), (0.548, 0.462), (0.530, 0.488)],
    # 胸下横线
    [(0.452, 0.352), (0.480, 0.362), (0.520, 0.362), (0.548, 0.352)],
]
layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
col = (232, 228, 220, 235)
wpx = max(3, int(W * 0.0032))
for pts in lines:
    d.line([P(x, y) for x, y in pts], fill=col, width=wpx, joint="curve")
layer = layer.filter(ImageFilter.GaussianBlur(0.8))
out = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
out.save(DST, quality=95)
print("drawn:", DST, im.size, "line width px:", wpx)
