# -*- coding: utf-8 -*-
"""把源图缩小后贴到更大的画布上（边缘像素外推填充），给 Kontext 留出全身空间。"""
import os
from PIL import Image

def edge_extend(im, W, H, cx, cy):
    """以 im 为中心贴在 W x H 画布上，四周用边缘像素外推填充。"""
    w, h = im.size
    canvas = Image.new("RGB", (W, H), im.getpixel((0, 0)))
    # 四条边外推
    top = im.crop((0, 0, w, 1)).resize((w, cy), Image.NEAREST) if cy > 0 else None
    bot = im.crop((0, h - 1, w, h)).resize((w, H - cy - h), Image.NEAREST) if H - cy - h > 0 else None
    left = im.crop((0, 0, 1, h)).resize((cx, h), Image.NEAREST) if cx > 0 else None
    right = im.crop((w - 1, 0, w, h)).resize((W - cx - w, h), Image.NEAREST) if W - cx - w > 0 else None
    if top: canvas.paste(top, (cx, 0))
    if bot: canvas.paste(bot, (cx, cy + h))
    if left: canvas.paste(left, (0, cy))
    if right: canvas.paste(right, (cx + w, cy))
    canvas.paste(im, (cx, cy))
    return canvas

def pad_image(src, dst, size=(896, 1152), fill=0.74):
    im = Image.open(src).convert("RGB")
    W, H = size
    w = int(W * fill); h = int(H * fill)
    sc = min(w / im.size[0], h / im.size[1])
    im2 = im.resize((max(1, int(im.size[0] * sc)), max(1, int(im.size[1] * sc))), Image.LANCZOS)
    cx = (W - im2.size[0]) // 2; cy = (H - im2.size[1]) // 2
    edge_extend(im2, W, H, cx, cy).save(dst, quality=95)
    return dst

if __name__ == "__main__":
    import sys
    print(pad_image(sys.argv[1], sys.argv[2]))
