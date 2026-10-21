# -*- coding: utf-8 -*-
"""Split each per-volume .txt into per-chapter HTML + DOCX files, organized
into volume subfolders, with per-volume and master index.html.

Input : "第一卷 龙蛇起陆.txt" ... "第八卷 登阶化仙.txt"  (zhiguge scrape output)
Output: OUTDIR/<卷名>/第NNN章 标题.{html,docx}
        OUTDIR/<卷名>/index.html
        OUTDIR/index.html
"""
import os, re, json, html as ihtml, zipfile, datetime
from xml.sax.saxutils import escape as xesc

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(WORKSPACE, "玄蛇成仙_分卷版")
BOOK_TITLE = "玄蛇成仙，从镇族老祖开始"
AUTHOR = "朝北海"

# volume order + display names (must match the .txt filenames)
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


def parse_chapters(text):
    """Return list of (num, title, body)."""
    # split on lines beginning with 第N章 (allow spaced NBSP variants)
    heads = list(re.finditer(r'(?m)^第\s*(\d+)\s*章[^\n]*', text))
    chapters = []
    for i, m in enumerate(heads):
        num = int(m.group(1))
        title = re.sub(r'\s+', ' ', m.group(0).strip())
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[start:end].strip()
        # drop a leading blank line already consumed by strip
        chapters.append((num, title, body))
    return chapters


# ---------- DOCX (pure stdlib OOXML) ----------
def docx_xml_escape(s):
    return xesc(s)


def make_docx(path, title, body):
    # styles: default east-asian font + a title style
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/>'
        '</w:rPr></w:rPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="ChapterTitle">'
        '<w:name w:val="ChapterTitle"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="240"/></w:pPr>'
        '<w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>'
        '</w:styles>'
    )
    # body paragraphs
    paras = []
    # title paragraph
    paras.append(
        '<w:p w:styleId="ChapterTitle"><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
        % docx_xml_escape(title))
    # content paragraphs (split on newlines)
    for line in body.split("\n"):
        line = line.rstrip()
        if line == "":
            # empty paragraph keeps spacing
            paras.append('<w:p><w:r><w:t xml:space="preserve"> </w:t></w:r></w:p>')
        else:
            paras.append('<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
                         % docx_xml_escape(line))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>' + "".join(paras) +
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
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
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", doc_rels)


# ---------- HTML ----------
HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{
    max-width: 760px; margin: 0 auto; padding: 2.2em 1.2em 4em;
    font-family: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", serif;
    font-size: 18px; line-height: 1.9; color: #1f1f1f; background: #fcfcfa;
  }}
  h1 {{ text-align: center; font-size: 1.5em; margin: 0 0 1.4em; font-weight: 700; }}
  .meta {{ text-align:center; color:#999; font-size:.85em; margin-bottom:2em; }}
  p {{ text-indent: 2em; margin: 0 0 .2em; white-space: pre-wrap; }}
  .nav {{ display:flex; justify-content:space-between; margin-top:3em; font-size:.9em; }}
  .nav a {{ color:#3a6ea5; text-decoration:none; }}
  .nav a:hover {{ text-decoration: underline; }}
  hr {{ border:none; border-top:1px solid #eee; margin:2.5em 0; }}
</style>
</head>
<body>
"""

HTML_FOOT = "</body></html>"


def make_html(path, title, body, prev_link, next_link):
    paras = "\n".join("<p>%s</p>" % ihtml.escape(p) for p in body.split("\n") if p.strip() != "")
    nav = '<div class="nav">'
    nav += '<a href="%s">← 上一章</a>' % prev_link if prev_link else '<span></span>'
    nav += '<a href="%s">下一章 →</a>' % next_link if next_link else '<span></span>'
    nav += "</div>"
    html = (HTML_HEAD.format(title=ihtml.escape(title)) +
            "<h1>%s</h1>\n" % ihtml.escape(title) +
            '<div class="meta">%s · %s</div>\n' % (ihtml.escape(BOOK_TITLE), ihtml.escape(AUTHOR)) +
            (paras + "\n" if paras else '<p style="text-align:center;color:#c33;">（本章抓取失败，待补）</p>\n') +
            nav + HTML_FOOT)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    summary = []
    for _start, vname in VOLUMES:
        src = os.path.join(WORKSPACE, vname + ".txt")
        if not os.path.exists(src):
            print("SKIP (missing):", src)
            continue
        text = open(src, encoding="utf-8-sig").read()
        chapters = parse_chapters(text)
        vdir = os.path.join(OUTDIR, vname)
        os.makedirs(vdir, exist_ok=True)
        files = []
        for idx, (num, title, body) in enumerate(chapters):
            prefix = "第%03d章 " % num
            sub = title
            mm = re.match(r'第\s*\d+\s*章\s*(.*)$', title)
            if mm:
                sub = mm.group(1).strip()
            fname = safe(prefix + sub)
            html_path = os.path.join(vdir, fname + ".html")
            docx_path = os.path.join(vdir, fname + ".docx")
            prev_link = None if idx == 0 else files[idx - 1][0]
            next_link = None  # fill after
            make_html(html_path, title, body, prev_link, None)
            make_docx(docx_path, title, body)
            files.append((safe(fname + ".html"), title, num))
        # second pass: fix next links
        for idx in range(len(files)):
            hp = os.path.join(vdir, files[idx][0])
            nxt = files[idx + 1][0] if idx + 1 < len(files) else None
            s = open(hp, encoding="utf-8").read()
            if nxt:
                s = s.replace('<a href="None">下一章 →</a>', '<a href="%s">下一章 →</a>' % nxt)
            else:
                s = s.replace('<a href="None">下一章 →</a>', '<span></span>')
            open(hp, "w", encoding="utf-8").write(s)
        # per-volume index.html
        items = "\n".join(
            '<li><a href="%s">%s</a></li>' % (fn, ihtml.escape(t)) for fn, t, _n in files)
        vidx = (HTML_HEAD.format(title=ihtml.escape(vname)) +
                "<h1>%s</h1>\n<div class='meta'>%s · %s · 共 %d 章</div>\n"
                "<hr>\n<ul>\n%s\n</ul>\n" % (
                    ihtml.escape(vname), ihtml.escape(BOOK_TITLE),
                    ihtml.escape(AUTHOR), len(files), items) + HTML_FOOT)
        open(os.path.join(vdir, "index.html"), "w", encoding="utf-8").write(vidx)
        summary.append((vname, vdir, len(files), len(chapters)))
        print("OK %s: %d chapters -> %s" % (vname, len(chapters), vdir))

    # master index.html
    vol_links = "\n".join(
        '<li><a href="%s/index.html">%s</a>（%d 章）</li>' % (safe(vname), ihtml.escape(vname), cnt)
        for vname, _vdir, cnt, _c in summary)
    master = (HTML_HEAD.format(title=ihtml.escape(BOOK_TITLE + " · 分卷目录")) +
              "<h1>%s</h1>\n<div class='meta'>%s · 共 %d 卷</div>\n<hr>\n<ul>\n%s\n</ul>\n"
              % (ihtml.escape(BOOK_TITLE), ihtml.escape(AUTHOR), len(summary), vol_links) +
              HTML_FOOT)
    open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(master)
    total = sum(c for _v, _d, c, _ch in summary)
    print("\nDONE. Total chapters split: %d across %d volumes -> %s" % (total, len(summary), OUTDIR))


if __name__ == "__main__":
    main()
