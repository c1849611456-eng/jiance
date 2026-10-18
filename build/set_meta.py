import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 3 轮：为三份 PDF 写入文档元数据（标题/作者/主题/关键词/创建者），并复检未被破坏。"""
import os, shutil
from pypdf import PdfReader, PdfWriter
DEL = str(paths.DELIVER)
BK = str(paths.BR + '/_backup_before_meta')
os.makedirs(BK, exist_ok=True)
META = {
 "效果图.pdf": dict(
    title="Brand · Series｜效果图 RENDERED VIEWS",
    author="Example Company · 泳装产品设计赛道参赛作品",
    subject="女装泳装系列 6 套（三海域 × 各 2 套）· 正视图/侧视图/45°视图/底视图/背面视图 + 细节特写",
    keywords="泳装;效果图;AI 设计;Brand;Series;A3;300dpi",
    creator="BRAND SERIES"),
 "作品说明.pdf": dict(
    title="Brand · Series｜作品说明 STATEMENT",
    author="Example Company · 泳装产品设计赛道参赛作品",
    subject="作品说明：灵感设计说明 + AI 运用过程说明 + 工作流示意 + 过程截图与质检记录",
    keywords="作品说明;AI 工具;工作流;泳装设计;Brand",
    creator="BRAND SERIES"),
 "技术图_Technical.pdf": dict(
    title="Brand · Series｜技术平面图 TECHNICAL FLATS",
    author="Example Company · 泳装产品设计赛道参赛作品",
    subject="六款泳装技术平面图（版型尺寸依据）",
    keywords="技术图;版型;平面图;泳装;Brand",
    creator="BRAND SERIES"),
}
for name, meta in META.items():
    p = os.path.join(DEL, name)
    if not os.path.exists(p): print("缺文件:", name); continue
    if not os.path.exists(os.path.join(BK, name)): shutil.copy2(p, os.path.join(BK, name))
    r = PdfReader(p); w = PdfWriter()
    for pg in r.pages: w.add_page(pg)
    w.add_metadata({"/Title": meta["title"], "/Author": meta["author"], "/Subject": meta["subject"],
                    "/Keywords": meta["keywords"], "/Creator": meta["creator"], "/Producer": "BRAND pipeline (pypdf)"})
    tmp = p + ".tmp"
    with open(tmp, "wb") as f: w.write(f)
    os.replace(tmp, p)
    r2 = PdfReader(p)
    m = r2.metadata or {}
    print("%s: 页数 %d 元数据 Title=%s" % (name, len(r2.pages), str(m.get("/Title"))[:40]), flush=True)
