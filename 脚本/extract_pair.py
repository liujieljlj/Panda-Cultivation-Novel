# -*- coding: utf-8 -*-
"""临时工具：把 html 正文段落抽成 txt，供 check_similarity / deep_scan / rhythm_scan 使用。
用法：python _extract_pair.py
"""
import re, os, sys, html as htmllib, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".workbuddy", "tmp_scan")
os.makedirs(OUT, exist_ok=True)


def extract(path):
    raw = open(path, encoding="utf-8").read()
    body = raw
    m = re.search(r"<body[^>]*>(.*)</body>", raw, re.S)
    if m:
        body = m.group(1)
    # 去掉脚本样式与导航
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
    lines = []
    for p in paras:
        t = re.sub(r"<[^>]+>", "", p)
        t = htmllib.unescape(t)
        t = t.replace("\u3000", "").strip()
        if t:
            lines.append(t)
    return "\n".join(lines)


def find(vol_dir, num):
    hits = glob.glob(os.path.join(vol_dir, "第%03d章 *.html" % num))
    return hits[0] if hits else None


vol_new = os.path.join(ROOT, "熊猫成仙，从青竹山开始", "第一卷 龙蛇起陆")
vol_old = os.path.join(ROOT, "玄蛇成仙_分卷版", "第一卷 龙蛇起陆")

num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
a = find(vol_old, num)
b = find(vol_new, num)
if not a or not b:
    print("找不到：", num, a, b)
    sys.exit(1)

ta, tb = extract(a), extract(b)
pa = os.path.join(OUT, "orig_%03d.txt" % num)
pb = os.path.join(OUT, "new_%03d.txt" % num)
open(pa, "w", encoding="utf-8").write(ta)
open(pb, "w", encoding="utf-8").write(tb)
print("原著：", a)
print("  段落", len(ta.splitlines()), "汉字", len(re.findall(r"[\u4e00-\u9fff]", ta)), "字符", len(ta))
print("新章：", b)
print("  段落", len(tb.splitlines()), "汉字", len(re.findall(r"[\u4e00-\u9fff]", tb)), "字符", len(tb))
print(pa)
print(pb)
