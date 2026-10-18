import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""手臂姿势镜像约定求解：试三种符号方案，用左右臂对称性数值自检挑最优，导出最优网格。"""
import json, math, os, sys
import numpy as np, torch, trimesh, anny
sys.path.insert(0, str(paths.D3D + '/scripts'))
import anny_body as AB
OUT = str(paths.D3D + '/out')
m = anny.Anny(local_changes="default", facial_actions="none").to(dtype=torch.float32)
labels = list(m.bone_labels)
UP = [l for l in labels if "upperarm" in l]

def build(mode):
    pose = torch.eye(4)[None, None].repeat(1, m.bone_count, 1, 1)
    for nm in UP:
        side = nm.split(".")[-1]
        sg = 1 if side.endswith("L") else -1
        if mode == "both":      sx, sz = sg, sg
        elif mode == "none":    sx, sz = 1, 1
        else:                   sx, sz = 1, sg      # z-only 镜像
        R = AB.rotmat("X", sx * AB.ARM_DX) @ AB.rotmat("Z", sz * AB.ARM_DZ)
        pose[0, labels.index(nm)] = R
    o = m(pose_parameters=pose, phenotype_kwargs=AB.PHENO, local_changes_kwargs=AB.LOCAL)
    v = o["vertices"].squeeze(0).detach().cpu().numpy()
    tm = trimesh.Trimesh(vertices=v, faces=m.faces, process=False)
    tm.vertices[:, 2] -= tm.vertices[:, 2].min()
    return tm

def sym(tm):
    v = tm.vertices; h = v[:, 2].max()
    arm = (v[:, 2] > 0.68 * h) & (v[:, 2] < 1.02 * h) & (np.abs(v[:, 0]) > 0.17)
    L = arm & (v[:, 0] > 0); R = arm & (v[:, 0] < 0)
    if L.sum() < 30 or R.sum() < 30: return None
    return float(abs(v[L, 2].mean() - v[R, 2].mean())), float(abs(np.abs(v[L, 0]).mean() - np.abs(v[R, 0]).mean()))

best = None
for mode in ("both", "none", "zonly"):
    tm = build(mode)
    r = sym(tm)
    print("模式 %-6s 对称偏差 dz=%.4f dx=%.4f" % (mode, r[0], r[1]) if r else "模式 %s 点数不足" % mode)
    if r and (best is None or (r[0] + r[1]) < best[1]):
        best = (mode, r[0] + r[1], tm)
print("最优模式:", best[0], "总偏差 %.4f" % best[1])
best[2].export(os.path.join(OUT, "anny_body.obj"))
print("已导出最优网格")
