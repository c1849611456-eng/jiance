import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""spec + 面板图 -> HTML -> Chrome -> 效果图_v2.pdf（带文字层）+ 逐页 PNG。"""
import os, sys, json, subprocess, html
import yaml
from string import Template
from pathlib import Path

BR = Path(str(paths.BR))
SPEC = BR / "spec" / "styles.yaml"
PANELS = BR / "build" / "panels"
OUT = BR / "out"; OUT.mkdir(parents=True, exist_ok=True)
PAGES = BR / "build" / "pages"; PAGES.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

spec = yaml.safe_load(open(SPEC, encoding="utf-8"))
palette = spec["palette"]
common = spec["common"]
manifest = spec["render_manifest"]
VIEW_LABEL = {"front": "正视图 FRONT", "side": "侧视图 SIDE", "back": "背面视图 BACK",
              "bottom": "底视图 BOTTOM ｜ 下装·腿口", "three_quarter": "45° 视图 THREE-QUARTER"}
ORDER = ["front", "side", "three_quarter", "bottom", "back"]

CSS = """
@page { size: 297mm 420mm; margin: 0; }
* { box-sizing: border-box; }
body { margin:0; background:#fff; font-family:"Microsoft YaHei","PingFang SC",sans-serif; color:#22262c; }
.page { position:relative; width:297mm; height:420mm; padding:12mm 14mm; overflow:hidden; page-break-after:always; background:#FCFBF9; }
.page:last-child { page-break-after:auto; }
.hd { display:flex; align-items:flex-end; justify-content:space-between; border-bottom:1.3pt solid #1E4E65; padding-bottom:1.8mm; height:16mm; }
.code { font-size:26pt; font-weight:700; color:#1E4E65; letter-spacing:1pt; }
.cn { font-size:19pt; font-weight:700; margin-left:3mm; }
.en { font-size:11pt; color:#68707a; margin-left:2.5mm; letter-spacing:.6pt; }
.hd-r { font-size:8.6pt; color:#3d454e; text-align:right; line-height:1.5; }
.views { display:grid; grid-template-columns:repeat(6, 1fr); gap:4mm 3mm; margin-top:3mm; }
.views .cell { grid-column: span 2; }
.views.five .cell:nth-child(4) { grid-column: 2 / span 2; }
.views.five .cell:nth-child(5) { grid-column: 4 / span 2; }
.cell img { width:72mm; height:96mm; display:block; margin:0 auto; background:#f1efeb; }
.cap { display:flex; justify-content:space-between; font-size:7.4pt; margin-top:1.1mm; border-top:.6pt solid #C9CDD2; padding-top:.7mm; }
.cap .r { color:#68707a; }
.cols { display:grid; grid-template-columns:1.02fr 1fr 1.12fr; gap:6mm; margin-top:4mm; height:88mm; }
.details { display:grid; grid-template-columns:repeat(4, 1fr); gap:4mm; margin-top:4mm; }
.detail img { width:100%; height:33mm; object-fit:cover; display:block; background:#f1efeb; }
.detail .dc { font-size:6.7pt; color:#3d4148; margin-top:.9mm; border-top:.4pt solid #E2E0DB; padding-top:.7mm; }
h3 { font-size:9pt; color:#1E4E65; margin:0 0 1.4mm 0; border-left:2.4pt solid #3D8D90; padding-left:2mm; }
h3.mt { margin-top:3.4mm; }
ul { margin:0; padding-left:3.6mm; }
li { font-size:7.5pt; line-height:1.52; margin-bottom:.9mm; }
table { width:100%; border-collapse:collapse; }
td, th { font-size:7.1pt; line-height:1.42; padding:.55mm 0; vertical-align:top; border-bottom:.4pt solid #E2E0DB; }
td.k { color:#4a5158; width:30%; }
th { text-align:left; color:#1E4E65; font-size:7.1pt; border-bottom:.7pt solid #9aa3ac; }
td.c { text-align:center; white-space:nowrap; padding-left:1mm; }
td.k { padding-right:1.5mm; }
td.v { padding-left:1mm; }
.sw { display:flex; gap:2mm; margin-bottom:2.2mm; }
.chip { flex:1; }
.chip .box { height:10.5mm; border:.4pt solid #D8D5CF; }
.chip .t { font-size:6.7pt; color:#3d454e; margin-top:.7mm; line-height:1.35; }
.note { font-size:6.6pt; color:#68707a; line-height:1.45; margin:1.4mm 0 0 0; }
.std { position:absolute; left:14mm; right:14mm; bottom:13mm; font-size:6.9pt; color:#3d454e; border-top:.9pt solid #1E4E65; padding-top:1.5mm; line-height:1.55; }
.ft { position:absolute; left:14mm; right:14mm; bottom:6mm; display:flex; justify-content:space-between; font-size:6.7pt; color:#7a8189; }
"""

PAGE = Template("""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>$code $name_cn</title>
<style>$css</style></head><body>
<div class="page">
  <div class="hd">
    <div><span class="code">$code</span><span class="cn">$name_cn</span><span class="en">$name_en</span></div>
    <div class="hd-r">$series<br>$scene</div>
  </div>
  <div class="views$viewcls">$cells</div>
  <div class="cols">
    <div class="col">
      <h3>结构说明 / CONSTRUCTION</h3><ul>$construction</ul>
      <h3 class="mt">关键成品尺寸 / KEY DIMENSIONS</h3><table>$keydims</table>
    </div>
    <div class="col">
      <h3>色彩规格 / COLOURWAY</h3><div class="sw">$swatches</div>
      <h3 class="mt">规格表 / SIZE CHART</h3><table>$sizetable</table>
      <p class="note">$sizenote</p>
    </div>
    <div class="col">
      <h3>材料与功能 / MATERIAL &amp; PERFORMANCE</h3><table>$materials</table>
      <h3 class="mt">功能指标 / CLAIMS</h3><table>$claims</table>
    </div>
  </div>
  <h3 style="margin-top:4mm">细节特写 / DESIGN DETAILS</h3>
  <div class="details">$details</div>
  <div class="std">$standards</div>
  <div class="ft"><span>$brand　|　效果图 RENDERED VIEWS</span><span>$version　·　A3 / 300 dpi / RGB　·　单位 mm　·　第 $pageno 页 / 共 $pagetotal 页</span></div>
</div></body></html>""")

def esc(s): return html.escape(str(s))

def build_page(st):
    code = st["code"]
    cells = []
    for v in ORDER:
        fn = manifest.get(code, {}).get(v)
        panel = PANELS / ("%s_%s.jpg" % (code, v))
        if not fn or not panel.exists():
            continue
        cells.append('<div class="cell"><img src="%s"><div class="cap"><span><b>%s</b></span><span class="r">%s</span></div></div>'
                     % (panel.as_uri(), VIEW_LABEL[v], esc(st["name_cn"] + " " + st["name_en"])))
    construction = "".join("<li>%s</li>" % esc(x) for x in st["construction"])
    keydims = "".join("<tr><td class='k'>%s</td><td>%s</td></tr>" % (esc(a), esc(b)) for a, b in st["key_dims"])
    sw = "".join('<div class="chip"><div class="box" style="background:%s"></div><div class="t">%s<br>%s · %s%%</div></div>'
                 % (c["hex"], esc(c["name"]), esc(c["hex"]), c["pct"]) for c in st["colors"])
    sc = common["size_chart"]
    head = "".join("<th%s>%s</th>" % (" class='c'" if i else "", esc(h)) for i, h in enumerate(sc["header"]))
    rows = "".join("<tr><td class='k'>%s</td>%s</tr>" % (esc(r[0]), "".join("<td class='c'>%s</td>" % esc(x) for x in r[1:])) for r in sc["rows"])
    sizetable = "<tr>%s</tr>%s" % (head, rows)
    materials = "".join("<tr><td class='k'>%s</td><td class='v'>%s</td></tr>" % (esc(a), esc(b + ("　" + str(c) if c and c != "—" else ""))) for a, b, c in st["materials"])
    claims = "".join("<tr><td class='k'>%s</td><td>%s<span style='color:#68707a'>（%s）</span></td></tr>" % (esc(a), esc(b), esc(d)) for a, b, d in st["claims"])
    det = []
    for i, d in enumerate(st.get("details", []), 1):
        p = BR / "build" / "details" / ("%s_d%d.jpg" % (code, i))
        if p.exists():
            det.append('<div class="detail"><img src="%s"><div class="dc">%s</div></div>' % (p.as_uri(), esc(d["label"])))
    details_html = "".join(det) or "<div></div>"
    std_items = common["standards_base"]
    standards = "<b>标准与检测 / STANDARDS</b>　" + "　｜　".join("%s：%s（%s）" % (esc(i["item"]), esc(i["value"]), esc(i["basis"])) for i in std_items) + "<br>" + esc(common["chlorine_note"])
    return PAGE.substitute(css=CSS, code=code, name_cn=st["name_cn"], name_en=st["name_en"], series=st["series"], scene=st["scene"],
                           cells="".join(cells), viewcls=(" five" if len(cells) == 5 else ""), construction=construction, keydims=keydims, swatches=sw,
                           sizetable=sizetable, sizenote=esc(sc["note"]), materials=materials, claims=claims,
                           standards=standards, details=details_html, brand=spec["brand"], version=spec["version"],
                           pageno=PAGENO.get(code, ""), pagetotal=str(len(spec["styles"])))

PAGENO = {st["code"]: str(i) for i, st in enumerate(spec["styles"], 1)}
pages = []
for st in spec["styles"]:
    doc = build_page(st)
    p = PAGES / ("%s.html" % st["code"])
    p.write_text(doc, encoding="utf-8")
    pages.append((st["code"], doc, p))
    print("page written:", p.name, len(doc), "chars")

combined = PAGES / "_all.html"
combined.write_text("<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><style>%s</style></head><body>%s</body></html>"
                    % (CSS, "".join(d.split("<body>", 1)[1].rsplit("</body>", 1)[0] for _, d, _ in pages)), encoding="utf-8")
print("combined:", combined)

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROME RC", r.returncode, r.stderr[-400:])
    return r

pdf = OUT / "效果图_v2.pdf"
run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
     "--print-to-pdf=" + str(pdf), combined.as_uri()])
print("pdf:", pdf, pdf.stat().st_size if pdf.exists() else "MISSING")

for code, _, p in pages:
    png = OUT / ("page_%s.png" % code)
    run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--force-device-scale-factor=3.125", "--window-size=1123,1588",
         "--screenshot=" + str(png), p.as_uri()])
    print("png:", png.name, png.stat().st_size if png.exists() else "MISSING")
