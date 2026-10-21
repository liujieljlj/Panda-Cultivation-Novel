# -*- coding: utf-8 -*-
"""Build HTML + DOCX for the panda-version novel (my own rewrite).

Source : 熊猫版_正文/第NNN章 标题.txt
Output : 熊猫成仙，从青竹山开始/<卷名>/第NNN章 标题.{html,docx}
         熊猫成仙，从青竹山开始/<卷名>/index.html
         熊猫成仙，从青竹山开始/index.html

Reusable: just drop more chapter .txt files into 熊猫版_正文/ and rerun.
"""
import os, re, glob, html as ihtml, zipfile
from xml.sax.saxutils import escape as xesc

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(WORKSPACE, "熊猫版_正文")
OUTDIR = os.path.join(WORKSPACE, "熊猫成仙，从青竹山开始")

BOOK_TITLE = "熊猫成仙，从青竹山开始"
AUTHOR = "改编自 朝北海《玄蛇成仙，从镇族老祖开始》"
PROTAGONIST = "陆明远"

# volume boundaries (chapter number -> volume folder name)
VOLUMES = [
    (1,   "第一卷 龙蛇起陆"),
    (51,  "第二卷 血海飘摇"),
    (115, "第三卷 南沧风起"),
    (189, "第四卷 玄皇镇世"),
    (314, "第五卷 朝风古界"),
    (457, "第六卷 离乱之主"),
    (551, "第七卷 天尊无量"),
    (675, "第八卷 登阶化仙"),
]

ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')


def safe(s):
    return ILLEGAL.sub("_", s).strip().rstrip(".")


def volume_of(num):
    name = VOLUMES[0][1]
    for start, v in VOLUMES:
        if num >= start:
            name = v
    return name


# ---------- DOCX (pure stdlib OOXML, CSS-matched) ----------
# 与 HTML 的 CSS 逐项对齐：
#   字体  serif  -> 宋体 / Times New Roman
#   字号  18px   -> 13.5pt (sz=27)
#   行距  1.95   -> w:line=468 auto
#   段距  .55em  -> after=149
#   缩进  2em    -> firstLineChars=200 / firstLine=540
#   标题  1.55em -> 21pt (sz=42) + 加粗 + 居中 + 字距 0.04em
#   副题  书名·主角，0.82em -> 11pt，灰色 #9A9A94，居中
FONT_EA = "宋体"
FONT_ASCII = "Times New Roman"
SZ_BODY, SZ_TITLE, SZ_META = "27", "42", "22"
LINE_BODY = "468"      # 1.95 倍行距
AFTER_BODY = "149"     # 0.55em
AFTER_TITLE = "460"    # 1.1em（相对 21pt）
AFTER_META = "531"     # 2.4em（相对 11pt）
IND_BODY = "540"       # 2em（相对 13.5pt）

RPR_BODY = ('<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s"/>'
            '<w:sz w:val="%s"/><w:szCs w:val="%s"/></w:rPr>'
            % (FONT_ASCII, FONT_ASCII, FONT_EA, FONT_ASCII, SZ_BODY, SZ_BODY))
RPR_TITLE = ('<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s"/>'
             '<w:b/><w:bCs/><w:spacing w:val="17"/>'
             '<w:sz w:val="%s"/><w:szCs w:val="%s"/></w:rPr>'
             % (FONT_ASCII, FONT_ASCII, FONT_EA, FONT_ASCII, SZ_TITLE, SZ_TITLE))
RPR_META = ('<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s"/>'
            '<w:color w:val="9A9A94"/><w:sz w:val="%s"/><w:szCs w:val="%s"/></w:rPr>'
            % (FONT_ASCII, FONT_ASCII, FONT_EA, FONT_ASCII, SZ_META, SZ_META))


def _para(text, kind="body"):
    """kind: title / meta / body. 直接内联全部格式，避免被编辑器二次保存时丢失。"""
    if kind == "title":
        ppr = ('<w:pPr><w:spacing w:before="0" w:after="%s"/>'
               '<w:ind w:firstLine="0" w:firstLineChars="0"/><w:jc w:val="center"/></w:pPr>'
               % AFTER_TITLE)
        rpr = RPR_TITLE
    elif kind == "meta":
        ppr = ('<w:pPr><w:spacing w:before="0" w:after="%s"/>'
               '<w:ind w:firstLine="0" w:firstLineChars="0"/><w:jc w:val="center"/></w:pPr>'
               % AFTER_META)
        rpr = RPR_META
    else:
        ppr = ('<w:pPr><w:spacing w:line="%s" w:lineRule="auto" w:after="%s"/>'
               '<w:ind w:firstLineChars="200" w:firstLine="%s"/></w:pPr>'
               % (LINE_BODY, AFTER_BODY, IND_BODY))
        rpr = RPR_BODY
    return ('<w:p>' + ppr + '<w:r>' + rpr +
            '<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % xesc(text))


def make_docx(path, title, body):
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s"/>'
        '<w:sz w:val="%s"/><w:szCs w:val="%s"/>'
        '</w:rPr></w:rPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:spacing w:line="%s" w:lineRule="auto" w:after="%s"/>'
        '<w:ind w:firstLineChars="200" w:firstLine="%s"/></w:pPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="ChapterTitle">'
        '<w:name w:val="ChapterTitle"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="0" w:after="%s"/>'
        '<w:ind w:firstLine="0" w:firstLineChars="0"/><w:jc w:val="center"/></w:pPr>'
        '<w:rPr><w:b/><w:sz w:val="%s"/><w:szCs w:val="%s"/></w:rPr></w:style>'
        '</w:styles>'
    ) % (FONT_ASCII, FONT_ASCII, FONT_EA, FONT_ASCII, SZ_BODY, SZ_BODY,
         LINE_BODY, AFTER_BODY, IND_BODY, AFTER_TITLE, SZ_TITLE, SZ_TITLE)

    paras = [_para(title, "title"),
             _para("%s · 主角：%s" % (BOOK_TITLE, PROTAGONIST), "meta")]
    for line in body.split("\n"):
        line = line.rstrip()
        if line == "":
            continue
        paras.append(_para(line, "body"))

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>' + "".join(paras) +
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1418" w:right="1134" w:bottom="1418" w:left="1134" '
        'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '</Types>'
    )
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", doc_rels)


# ---------- HTML ----------
PAGE_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --ink:#1f1f1f; --paper:#fcfcfa; --dim:#9a9a94; --link:#3a6ea5; }}
  body {{
    max-width: 780px; margin: 0 auto; padding: 2.4em 1.3em 4.5em;
    font-family: "Noto Serif CJK SC","Source Han Serif SC","Songti SC","SimSun",serif;
    font-size: 18px; line-height: 1.95; color: var(--ink); background: var(--paper);
  }}
  h1 {{ text-align:center; font-size:1.55em; margin:0 0 1.1em; font-weight:700; letter-spacing:.04em; }}
  .meta {{ text-align:center; color:var(--dim); font-size:.82em; margin-bottom:2.4em; letter-spacing:.05em; }}
  p {{ text-indent:2em; margin:0 0 .55em; }}
  .nav {{ display:flex; justify-content:space-between; margin-top:3.2em;
         padding-top:1.4em; border-top:1px solid #eceae4; font-size:.9em; }}
  .nav a {{ color:var(--link); text-decoration:none; }}
  .nav a:hover {{ text-decoration:underline; }}
  ul.toc {{ list-style:none; padding:0; }}
  ul.toc li {{ margin:.55em 0; }}
  ul.toc a {{ color:var(--ink); text-decoration:none; border-bottom:1px dotted #ccc; }}
  ul.toc a:hover {{ color:var(--link); }}
</style>
</head>
<body>
"""


def page(title, inner):
    return PAGE_HEAD.format(title=ihtml.escape(title)) + inner + "\n</body></html>"


def chapter_html(title, body, prev_link, next_link):
    paras = "\n".join("<p>%s</p>" % ihtml.escape(p) for p in body.split("\n") if p.strip())
    nav = '<div class="nav">'
    nav += '<a href="%s">← 上一章</a>' % prev_link if prev_link else "<span>　</span>"
    nav += "<span>%s</span>" % ihtml.escape(PROTAGONIST)
    nav += '<a href="%s">下一章 →</a>' % next_link if next_link else "<span>　</span>"
    nav += "</div>"
    inner = ("<h1>%s</h1>\n<div class='meta'>%s · 主角：%s</div>\n%s\n%s"
             % (ihtml.escape(title), ihtml.escape(BOOK_TITLE),
                ihtml.escape(PROTAGONIST), paras, nav))
    return page(title, inner)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    srcs = sorted(glob.glob(os.path.join(SRC_DIR, "第*章*.txt")))
    if not srcs:
        print("no source chapters in", SRC_DIR)
        return

    # collect
    chapters = []
    for p in srcs:
        text = open(p, encoding="utf-8-sig").read()
        lines = [l.rstrip() for l in text.split("\n")]
        title = ""
        for l in lines:
            if l.strip().startswith("第") and "章" in l:
                title = l.strip()
                break
        num = int(re.search(r'第\s*(\d+)\s*章', title).group(1))
        body = "\n".join(lines[lines.index(title) + 1:]).strip()
        chapters.append((num, title, body))
    chapters.sort(key=lambda x: x[0])

    # group by volume
    by_vol = {}
    for num, title, body in chapters:
        by_vol.setdefault(volume_of(num), []).append((num, title, body))

    total = 0
    summary = []
    for _start, vname in VOLUMES:
        if vname not in by_vol:
            continue
        items = by_vol[vname]
        vdir = os.path.join(OUTDIR, vname)
        os.makedirs(vdir, exist_ok=True)
        files = []
        for num, title, body in items:
            fname = safe("第%03d章 %s" % (num, re.sub(r'^第\s*\d+\s*章\s*', '', title)))
            files.append((num, title, body, fname))
        # write with prev/next
        for i, (num, title, body, fname) in enumerate(files):
            prev_link = files[i - 1][3] + ".html" if i > 0 else None
            next_link = files[i + 1][3] + ".html" if i + 1 < len(files) else None
            open(os.path.join(vdir, fname + ".html"), "w", encoding="utf-8").write(
                chapter_html(title, body, prev_link, next_link))
            make_docx(os.path.join(vdir, fname + ".docx"), title, body)
        # volume index
        li = "\n".join('<li><a href="%s.html">%s</a></li>' % (f[3], ihtml.escape(f[1]))
                       for f in files)
        vidx = ("<h1>%s</h1>\n<div class='meta'>%s · 共 %d 章</div>\n<ul class='toc'>\n%s\n</ul>"
                % (ihtml.escape(vname), ihtml.escape(BOOK_TITLE), len(files), li))
        open(os.path.join(vdir, "index.html"), "w", encoding="utf-8").write(
            page(vname, vidx))
        summary.append((vname, len(files)))
        total += len(files)
        print("OK %s: %d 章" % (vname, len(files)))

    # master index
    li = "\n".join('<li><a href="%s/index.html">%s</a>（%d 章）</li>'
                   % (safe(v), ihtml.escape(v), c) for v, c in summary)
    master = ("<h1>%s</h1>\n<div class='meta'>主角：%s · %s · 已成稿 %d 卷 %d 章</div>\n"
              "<ul class='toc'>\n%s\n</ul>"
              % (ihtml.escape(BOOK_TITLE), ihtml.escape(PROTAGONIST),
                 ihtml.escape(AUTHOR), len(summary), total, li))
    open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(
        page(BOOK_TITLE, master))
    print("\nDONE. %d 章 -> %s" % (total, OUTDIR))


if __name__ == "__main__":
    main()
