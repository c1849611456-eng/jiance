import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""作品说明.pdf 赛道合规核对：页数/体积/正文字数/是否含过程截图。"""
import os, re, sys
PDF = str(paths.DELIVER + '/作品说明.pdf')
print("存在:", os.path.exists(PDF), "体积: %.2f MB" % (os.path.getsize(PDF) / 1048576) if os.path.exists(PDF) else "缺失")
text = ""; nimg = 0; npage = 0
try:
    import fitz
    d = fitz.open(PDF); npage = d.page_count
    for p in d:
        text += p.get_text()
        nimg += len(p.get_images(full=True))
    print("解析库: PyMuPDF")
except Exception as e1:
    try:
        from pypdf import PdfReader
        r = PdfReader(PDF); npage = len(r.pages)
        for p in r.pages:
            text += p.extract_text() or ""
            try: nimg += len(p.images)
            except Exception: pass
        print("解析库: pypdf")
    except Exception as e2:
        print("无可用解析库:", type(e1).__name__, type(e2).__name__); sys.exit(0)
print("页数:", npage, " 内嵌图片数:", nimg)
cn = len(re.findall(r"[\u4e00-\u9fff]", text))
print("中文字符总数: %d（含标题/表头等）" % cn)
# 粗分节
def sect(name, nxt=None):
    i = text.find(name)
    if i < 0: return None
    j = text.find(nxt, i + len(name)) if nxt else len(text)
    seg = text[i + len(name): j if j > 0 else len(text)]
    return len(re.findall(r"[\u4e00-\u9fff]", seg)), seg[:60].replace("\n", " ")
for nm in ["灵感设计说明", "设计说明", "AI 运用过程说明", "AI运用过程说明", "运用过程说明", "AI 工具", "工作流"]:
    r = sect(nm)
    if r: print("  节「%s」: %d 字  开头: %s" % (nm, r[0], r[1]))
print("---- 正文前 600 字预览 ----")
print(text[:600].replace("\n", " "))
