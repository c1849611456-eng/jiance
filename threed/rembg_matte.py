# -*- coding: utf-8 -*-
"""专业抠图（rembg）：B1 正视去背 -> 合成纯色影棚背景。"""
import os
import numpy as np
from PIL import Image
from rembg import remove, new_session

SRC = r"D:\创新大赛\dafuer\_bridge\gen\b1_new\B1_new_front.png"
DST = r"D:\创新大赛\dafuer\_bridge\gen\b1_new\B1_front_matted.png"
model = os.environ.get("RMBG_MODEL", "u2net")
print("model:", model, flush=True)
session = new_session(model)
im = Image.open(SRC).convert("RGB")
cut = remove(im, session=session, alpha_matting=True,
             alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=15,
             alpha_matting_erode_size=8)
W, H = cut.size
alpha = np.asarray(cut.split()[-1], dtype=np.float32) / 255.0
print("前景占比 %.3f" % alpha.mean(), flush=True)
a = np.asarray(im, dtype=np.float32)
yy = np.linspace(0, 1, H)[:, None]
bg = (np.array([220., 220., 221.])[None, :] * (1 - yy) + np.array([248., 248., 248.])[None, :] * yy)
bg = np.repeat(bg[:, None, :], W, axis=1)
out = (a * alpha[:, :, None] + bg * (1 - alpha[:, :, None])).astype(np.uint8)
Image.fromarray(out).save(DST, quality=96)
print("saved", DST, flush=True)
