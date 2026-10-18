# -*- coding: utf-8 -*-
"""合规自检：检测躯干区域是否出现大面积裸露肤色（肤色像素占比阈值）。"""
import sys
import numpy as np
from PIL import Image
p = sys.argv[1]
im = Image.open(p).convert("RGB")
a = np.asarray(im, dtype=np.float32)
ycc = np.asarray(im.convert("YCbCr"), dtype=np.float32)
Y, Cb, Cr = ycc[:, :, 0], ycc[:, :, 1], ycc[:, :, 2]
skin = (Cb > 77) & (Cb < 135) & (Cr > 133) & (Cr < 180) & (Y > 40)
H, W = skin.shape
# 躯干带：人物大致居中的中段；取画面中央 40% 宽、纵向 30%~60% 高
band = skin[int(0.30*H):int(0.62*H), int(0.30*W):int(0.70*W)]
# 蓝色衣片
blue = (a[:,:,2] > 110) & (a[:,:,2] - a[:,:,0] > 35)
bband = blue[int(0.30*H):int(0.62*H), int(0.30*W):int(0.70*W)]
ratio = band.mean(); bratio = bband.mean()
print("躯干带：肤色 %.1f%%  蓝色衣片 %.1f%%" % (100*ratio, 100*bratio))
print("判定:", "不合规（裸露风险）" if (ratio > 0.22 and bratio < 0.25) else "通过")
