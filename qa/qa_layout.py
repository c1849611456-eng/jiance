import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 11 轮：六页版面结构自检（面板数/细节条/表格/标签/异常串）。"""
import os, re
PG = str(paths.BR + '/build' + '/pages')
BAD = ["None", "nan", "TODO", "{", "}", "undefined", "占位"]
print("| 款 | 面板格 | 细节图 | 表格 | 视角标签 | 异常串 |")
print("|---|---|---|---|---|---|")
for c in ["A1","A2","B1","B2","C1","C2"]:
    h = open(os.path.join(PG, "%s.html" % c), encoding="utf-8").read()
    cells = h.count('<div class="cell">')
    det = len(re.findall(r'class="detail"', h)) or h.count('details-row')
    tables = h.count("<table")
    labels = re.findall(r'<div class="cap">([^<]+)</div>', h) or re.findall(r'<b>([^<]+)</b>', h)
    views = [l for l in labels if any(k in l for k in ("正视图","侧视图","45°","底视图","背面视图"))]
    bad = [b for b in BAD if b in h]
    print("| %s | %d | %d | %d | %d 个: %s | %s |" % (c, cells, det, tables, len(views),
          "/".join(v.split()[0] for v in views), (", ".join(bad) if bad else "无")))
    # 表格行数
    rows = len(re.findall(r"<tr>", h))
    print("     表格行合计 %d ；页面字符数 %d" % (rows, len(h)))
