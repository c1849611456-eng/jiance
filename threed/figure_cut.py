import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""用 OpenCV 抠出 B1 正视人物（最大连通域 + 填洞 + 羽化），合成到纯色影棚背景。"""
import os
import numpy as np
import cv2
from PIL import Image
SRC = r"paths.BR\gen\b1_new\B1_new_front.png"
DST = r"paths.BR\gen\b1_new\B1_front_clean.png"
bgr = cv2.imdecode(np.fromfile(SRC, dtype=np.uint8), cv2.IMREAD_COLOR)   # 中文路径需用 imdecode
H, W = bgr.shape[:2]
print("size", W, H)
# 1) 背景色估计（左右边带）
edge = np.concatenate([bgr[:, :int(W*0.05)].reshape(-1,3), bgr[:, int(W*0.95):].reshape(-1,3)], axis=0)
bg = np.median(edge, axis=0)
diff = np.linalg.norm(bgr.astype(np.float32) - bg[None, None, :], axis=2)
fg = (diff > 52).astype(np.uint8)   # 提高阈值：把花纹背景的浅色斑块排除掉
# 2) 形态学（小核，速度快）
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k, iterations=2)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, k, iterations=2)
# 3) 最大连通域
n, lab, stats, cent = cv2.connectedComponentsWithStats(fg, 8)
if n > 1:
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    fg = (lab == idx).astype(np.uint8)
print("fg ratio %.3f" % fg.mean())
# 4) 填洞（对掩膜取反后从边界 floodFill）
inv = (1 - fg).astype(np.uint8)
ff = inv.copy()
mask2 = np.zeros((H + 2, W + 2), np.uint8)
cv2.floodFill(ff, mask2, (0, 0), 2)
holes = (ff == 1).astype(np.uint8)          # 未连到边界的背景 = 内部孔洞
fg = np.clip(fg + holes, 0, 1)
# 5) 羽化
alpha = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 2.4)[:, :, None]
# 6) 纯色影棚背景（上浅灰 -> 下白）
yy = np.linspace(0, 1, H)[:, None]
bgn = (np.array([221., 221., 222.])[None, :] * (1 - yy) + np.array([249., 249., 249.])[None, :] * yy)
bgn = np.repeat(bgn[:, None, :], W, axis=1)   # BGR 近似灰
out = (bgr.astype(np.float32) * alpha + bgn * (1 - alpha)).astype(np.uint8)
cv2.imencode('.jpg', out, [int(cv2.IMWRITE_JPEG_QUALITY), 96])[1].tofile(DST)   # 中文路径需用 imencode
print("saved", DST)
