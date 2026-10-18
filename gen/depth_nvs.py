# -*- coding: utf-8 -*-
"""深度驱动低机位合成 v5（修正人物掩膜与深度映射）
- 人物掩膜：颜色背景差分（不依赖深度阈值，因为近处地面比人体更"近"）
- 人体深度：把人物区域内的相对深度线性映射到 35 cm 深度板
- 背景：正对相机平面（z_far）的单应变换
- 统一仿射重取景 A，使人物高度 = fig_fill*H
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageFilter

def fig_mask(im, thr=26):
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w, _ = a.shape
    m = max(8, int(0.03 * min(h, w)))
    border = np.concatenate([a[:m].reshape(-1, 3), a[-m:].reshape(-1, 3), a[:, :m].reshape(-1, 3), a[:, -m:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    d = np.sqrt(((a - bg) ** 2).sum(axis=2))
    mask = d > thr
    mi = Image.fromarray((mask * 255).astype(np.uint8))
    mi = mi.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    mi = mi.filter(ImageFilter.MaxFilter(5))
    mask = np.asarray(mi) > 127
    # 保留最大连通域（用行/列投影近似：取 y 范围内占多数者）
    ys = np.where(mask.sum(axis=1) > 0.03 * w)[0]
    if len(ys) == 0: return mask
    keep = np.zeros_like(mask); keep[ys.min():ys.max() + 1] = mask[ys.min():ys.max() + 1]
    return keep

def solve_h(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.asarray(A, dtype=np.float64))
    return Vt[-1].reshape(3, 3)

def render(rgb_path, depth_path, out_path, cam0_h=1.15, cam1_h=0.30, pitch=26.0, fov=35.0,
           z_far=4.4, body_depth=0.35, out_size=(896, 1152), fig_fill=0.88):
    W, H = out_size
    im = Image.open(rgb_path).convert("RGB").resize(out_size, Image.LANCZOS)
    rgb = np.asarray(im, dtype=np.float32)
    d = np.asarray(Image.open(depth_path).convert("L").resize(out_size, Image.BILINEAR), dtype=np.float32) / 255.0
    dn = (d - d.min()) / (d.max() - d.min() + 1e-6)
    fm = fig_mask(im)
    if fm.sum() < 2000:
        print("  figure mask too small"); return None
    # HEAD_FLATTEN：头部（人物掩膜顶部 14% 高度）的深度取该区域中位数，避免头发被当成"更近"而把头顶拉大
    ys_f = np.where(fm.sum(axis=1) > 0.01 * W)[0]
    head_flat = False
    if len(ys_f) > 50:
        h_top, h_bot = ys_f[0], ys_f[-1]
        h_cut = int(h_top + 0.14 * (h_bot - h_top))
        head_zone = np.zeros_like(fm); head_zone[h_top:h_cut] = fm[h_top:h_cut]
        if head_zone.sum() > 500:
            dn = dn.copy(); dn[head_zone] = float(np.median(dn[head_zone])); head_flat = True
            print("  head depth flattened (%d px)" % int(head_zone.sum()))
    lo, hi = np.percentile(dn[fm], 5), np.percentile(dn[fm], 95)
    tf = np.clip((dn - lo) / max(1e-6, hi - lo), 0, 1)
    z = np.where(fm, z_far - tf * body_depth, z_far)
    f = 0.5 * H / math.tan(math.radians(fov / 2.0))
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    th = math.radians(pitch)
    uu, vv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    x = (uu - cx) / f * z
    y = -(vv - cy) / f * z
    def proj(X, Y, Z):
        Yc = (Y + cam0_h) - cam1_h
        X1 = X
        Y1 = Yc * math.cos(th) + (-Z) * math.sin(th)
        Z1 = -Yc * math.sin(th) + (-Z) * math.cos(th)
        zc = -Z1
        return f * X1 / np.maximum(zc, 1e-3) + cx, -f * Y1 / np.maximum(zc, 1e-3) + cy, zc
    su, sv, szc = proj(x, y, z)
    ok = fm & (szc > 0.3)
    x0, x1 = su[ok].min(), su[ok].max(); y0, y1 = sv[ok].min(), sv[ok].max()
    print("  diag: fig_px=%d proj_bbox=%.0f,%.0f,%.0f,%.0f" % (fm.sum(), x0, y0, x1, y1))
    s = (fig_fill * H) / max(1.0, (y1 - y0)); ccx = (x0 + x1) / 2.0
    def A(u, v): return (u - ccx) * s + W / 2.0, (v - y1) * s + H * 0.96
    bz = np.full_like(dn, z_far)
    bx = (uu - cx) / f * bz; by = -(vv - cy) / f * bz
    bu, bv, _ = proj(bx, by, bz)
    bu2, bv2 = A(bu, bv)
    Hm = solve_h([(0, 0), (W - 1, 0), (W - 1, H - 1), (0, H - 1)],
                 [(float(bu2[0, 0]), float(bv2[0, 0])), (float(bu2[0, W - 1]), float(bv2[0, W - 1])),
                  (float(bu2[H - 1, W - 1]), float(bv2[H - 1, W - 1])), (float(bu2[H - 1, 0]), float(bv2[H - 1, 0]))])
    Hi = np.linalg.inv(Hm); Hi = Hi / Hi[2, 2]
    a0 = np.asarray(im, dtype=np.float32)
    m0 = max(6, int(0.02 * min(H, W)))
    border0 = np.concatenate([a0[:m0].reshape(-1, 3), a0[-m0:].reshape(-1, 3), a0[:, :m0].reshape(-1, 3), a0[:, -m0:].reshape(-1, 3)])
    fillc = tuple(int(v) for v in np.median(border0, axis=0))
    bg = np.asarray(im.transform(out_size, Image.PERSPECTIVE, tuple(Hi.flatten()[:8]), resample=Image.BICUBIC,
                                 fillcolor=fillc), dtype=np.float32).copy()
    tu, tv = A(su, sv)
    ui = np.round(tu).astype(np.int32); vi = np.round(tv).astype(np.int32)
    inside = ok & (ui >= 0) & (ui < W) & (vi >= 0) & (vi < H)
    zbuf = np.full((H, W), 1e9, dtype=np.float32); mask = np.zeros((H, W), dtype=bool)
    order = np.argsort(-szc[inside])
    U = ui[inside][order]; V = vi[inside][order]; C = rgb[inside][order]; Z = szc[inside][order]
    out = bg
    for k in range(len(U)):
        yy, xx = V[k], U[k]
        if Z[k] < zbuf[yy, xx]:
            zbuf[yy, xx] = Z[k]; out[yy, xx] = C[k]; mask[yy, xx] = True
    for _ in range(14):
        if mask.all(): break
        grew = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(out, dy, 0), dx, 1); sm = np.roll(np.roll(mask, dy, 0), dx, 1)
            take = (~mask) & sm
            if take.any(): out[take] = sh[take]; mask = mask | take; grew = True
        if not grew: break
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4)).save(out_path, quality=95)
    print("  saved %s (pitch=%.0f cam1=%.2f)" % (os.path.basename(out_path), pitch, cam1_h))
    return out_path

if __name__ == "__main__":
    a = sys.argv
    render(a[1], a[2], a[3], pitch=float(a[4]) if len(a) > 4 else 26.0, cam1_h=float(a[5]) if len(a) > 5 else 0.30)
