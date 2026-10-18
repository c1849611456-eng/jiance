import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""RMBG-1.4 (ONNX, 经 hf-mirror 下载) 抠图 -> 合成纯色影棚背景。"""
import os, time
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL = os.path.join(paths.COMFY, "models", "rmbg", "model.onnx")
SRC = r"paths.BR\gen\b1_new\B1_new_front.png"
DST = r"paths.BR\gen\b1_new\B1_front_matted.png"
os.makedirs(os.path.dirname(MODEL), exist_ok=True)

if not os.path.exists(MODEL):
    import urllib.request
    url = "https://hf-mirror.com/briaai/RMBG-1.4/resolve/main/onnx/model.onnx"
    print("downloading", url, flush=True)
    t = time.time()
    urllib.request.urlretrieve(url, MODEL)
    print("downloaded %.1f MB in %.0fs" % (os.path.getsize(MODEL) / 1048576, time.time() - t), flush=True)

sess = ort.InferenceSession(MODEL, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
print("providers:", sess.get_providers(), flush=True)
iname = sess.get_inputs()[0].name
im = Image.open(SRC).convert("RGB")
W, H = im.size
x = np.asarray(im.resize((1024, 1024), Image.BILINEAR), dtype=np.float32) / 255.0
x = (x - 0.5) / 1.0
x = np.transpose(x, (2, 0, 1))[None, ...].astype(np.float32)
out = sess.run(None, {iname: x})[0]
print("out shape", out.shape, flush=True)
m = out[0][0]
m = 1.0 / (1.0 + np.exp(-m)) if m.min() < 0 or m.max() > 1 else m
mm = (np.clip(m, 0, 1) * 255).astype(np.uint8)
alpha = np.asarray(Image.fromarray(mm).resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0
print("foreground ratio %.3f" % alpha.mean(), flush=True)
a = np.asarray(im, dtype=np.float32)
yy = np.linspace(0, 1, H)[:, None]
bg = (np.array([219., 219., 220.])[None, :] * (1 - yy) + np.array([248., 248., 248.])[None, :] * yy)
bg = np.repeat(bg[:, None, :], W, axis=1)
res = (a * alpha[:, :, None] + bg * (1 - alpha[:, :, None])).astype(np.uint8)
Image.fromarray(res).save(DST, quality=96)
print("saved", DST, flush=True)
