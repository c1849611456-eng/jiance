import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 4 轮（复核）：确认重出后的 JPG 与页面 PNG 一致，并检查原 JPG 是否本来就"空白/异常"。"""
import os
import numpy as np, cv2
DEL = str(paths.DELIVER); JPG = os.path.join(DEL, "效果图_JPG"); OUT = str(paths.OUT)
BK = str(paths.BR + '/_backup_jpg_before')
rd = lambda p: cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
print("| 款 | JPG 均值/标准差 | PNG 均值/标准差 | 相关系数 | 判定 |")
print("|---|---|---|---|---|")
for c in ["A1","A2","B1","B2","C1","C2"]:
    j = os.path.join(JPG, "%s.jpg" % c); p = os.path.join(OUT, "page_%s.png" % c)
    a = rd(j); b = rd(p)
    ga = cv2.cvtColor(cv2.resize(a, (400, 566)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, (400, 566)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    cc = float(np.corrcoef(ga.ravel(), gb.ravel())[0, 1])
    print("| %s | %.0f/%.0f | %.0f/%.0f | %.5f | %s |" % (c, ga.mean(), ga.std(), gb.mean(), gb.std(), cc,
          "✅" if cc >= 0.995 else "⚠️"))
