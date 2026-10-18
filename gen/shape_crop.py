import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
src = str(paths.D3D + '/A1_flatlay_final.png')
im = Image.open(src).convert("RGB")
a = np.asarray(im.convert("L"))
mask = a < 200
ys, xs = np.where(mask)
print("bbox", xs.min(), ys.min(), xs.max(), ys.max(), im.size)
# 左半 = 前片
mid = (xs.min() + xs.max()) // 2
sel = xs < mid
x0, x1 = xs[sel].min(), xs[sel].max(); y0, y1 = ys[sel].min(), ys[sel].max()
pad = 60
box = (max(0, x0 - pad), max(0, y0 - pad), min(im.size[0], x1 + pad), min(im.size[1], y1 + pad))
crop = im.crop(box)
# 放到白底方图里
side = max(crop.size) + 120
canvas = Image.new("RGB", (side, side), (255, 255, 255))
canvas.paste(crop, ((side - crop.size[0]) // 2, (side - crop.size[1]) // 2))
canvas.resize((896, 896)).save(str(paths.COMFY + '/input' + '/shape_A1_front.png'))
canvas.save(str(paths.BR + '/gen' + '/nomodel/3d/shape_A1_front.png'))
print("saved shape input", canvas.size)
