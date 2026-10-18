import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 3 轮：确定性核验 —— 用当前正视图重新裁一次下装细节，与现用底视图逐像素比对。"""
import os, shutil
import numpy as np, cv2
GEN = str(paths.BR + '/gen')
R2 = str(paths.R2)
BK = str(paths.BR + '/_backup_bottom_before_recheck')
os.makedirs(BK, exist_ok=True)
CODES = ["A1", "A2", "B1", "B2", "C1", "C2"]
rd = lambda p: cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
print("| 款 | 与现用底视图差异(MAE) | 相关系数 | 判定 |")
print("|---|---|---|---|")
for c in CODES:
    cur = os.path.join(R2, "%s_bottom_low.png" % c)
    new = os.path.join(GEN, "%s_bottom_hem.png" % c)
    if not (os.path.exists(cur) and os.path.exists(new)):
        print("| %s | — | — | 缺文件 |" % c); continue
    if not os.path.exists(os.path.join(BK, "%s_bottom_low.png" % c)):
        shutil.copy2(cur, os.path.join(BK, "%s_bottom_low.png" % c))
    a = rd(cur); b = rd(new)
    if a.shape != b.shape: b = cv2.resize(b, (a.shape[1], a.shape[0]))
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32); gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mae = float(np.abs(ga - gb).mean())
    cc = float(np.corrcoef(ga.ravel(), gb.ravel())[0, 1])
    v = "✅ 一致" if cc >= 0.98 else ("⚠️ 有差异" if cc >= 0.90 else "❌ 现用图为旧版")
    print("| %s | %.2f | %.4f | %s |" % (c, mae, cc, v))
    if cc < 0.98:   # 现用图非当前正视所裁 -> 用新裁的替换
        shutil.copy2(new, cur)
        print("   已用新裁图替换 %s_bottom_low.png" % c, flush=True)
