# -*- coding: utf-8 -*-
"""Scrape one volume into its own txt file. Run one instance per volume,
in parallel (different volumes -> different output files, no conflicts).

Usage:  python scrape_vol.py <vol_index 0..7>
"""
import os, re, sys, time, json, random
import urllib.request
import html as ihtml

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
REF = "https://www.zhiguge.com/4nz3/l438o9/"
BASE_DOMAIN = "https://www.zhiguge.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# (start_chapter, folder/volume_name)  -- sorted by start_chapter
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


def get(u, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                u, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
                            "Referer": REF})
            return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 1.0)  # exponential-ish backoff
    return None


def norm_title(t):
    t = re.sub(r'第(\d+)\s*章', r'第\1章', t)
    return t.strip()


def extract_chapter(html):
    m = re.search(r'<div id="chapter">(.*?)</div>', html, re.S)
    if not m:
        return None
    raw = m.group(1)
    h = re.search(r'<h1>(.*?)</h1>', html, re.S)
    title = norm_title(h.group(1)) if h else ""
    txt = re.sub(r'<br\s*/?>', '\n', raw, flags=re.I)
    txt = re.sub(r'<[^>]+>', '', txt)
    txt = ihtml.unescape(txt).replace('\xa0', ' ')
    txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
    txt = re.sub(r'[ \t]+\n', '\n', txt)
    return title, txt


def fetch_chapter(url):
    html = get(url)
    if not html:
        return None
    res = extract_chapter(html)
    if not res:
        return None
    title, body = res
    # intra-chapter sub-pages like 8n5w4yg4c_2.html
    base = url.rsplit('/', 1)[1].split('.')[0]
    subs = re.findall(r'href="([^"]*' + re.escape(base) + r'_(\d+)\.html)"', html)
    seen_sub = set()
    for href, _n in sorted(subs, key=lambda x: int(x[1])):
        if href in seen_sub:
            continue
        seen_sub.add(href)
        if href.startswith('http'):
            sub_url = href
        elif href.startswith('/'):
            sub_url = BASE_DOMAIN + href
        else:
            sub_url = REF + href
        shtml = get(sub_url)
        if shtml:
            sres = extract_chapter(shtml)
            if sres and sres[1]:
                body += "\n" + sres[1]
    return title, body


def main():
    vi = int(sys.argv[1])
    start, name = VOLUMES[vi]
    end = VOLUMES[vi + 1][0] - 1 if vi + 1 < len(VOLUMES) else 10 ** 9

    with open(os.path.join(WORKSPACE, "chapters.json"), encoding="utf-8") as f:
        chs = json.load(f)
    sel = sorted([c for c in chs if start <= c[0] <= end], key=lambda x: x[0])

    # stagger parallel processes a bit to ease server load
    time.sleep(vi * 1.2 + random.uniform(0, 1.5))

    out_path = os.path.join(WORKSPACE, name + ".txt")
    log_path = os.path.join(WORKSPACE, "scrape_vol_%d.log" % vi)
    open(log_path, "w", encoding="utf-8").close()

    fails = []
    with open(out_path, "w", encoding="utf-8-sig") as out:
        out.write("%s\n作者：朝北海\n\n" % name)
        total = len(sel)
        for i, (num, url, _title) in enumerate(sel, 1):
            res = fetch_chapter(url)
            if not res or not res[1]:
                fails.append(num)
                out.write("\n第%d章 [抓取失败]\n\n" % num)
                with open(log_path, "a", encoding="utf-8") as lg:
                    lg.write("FAIL %d %s\n" % (num, url))
                time.sleep(0.5)
                continue
            t, b = res
            out.write("\n%s\n\n%s\n\n" % (t, b))
            with open(log_path, "a", encoding="utf-8") as lg:
                lg.write("OK %d/%d %s\n" % (i, total, t))
            time.sleep(0.4 + 0.3 * (hash(url) % 5) / 5.0)

    with open(log_path, "a", encoding="utf-8") as lg:
        lg.write("DONE vol %d (%s): total=%d fails=%d\n" % (vi, name, total, len(fails)))
    print("VOL %d (%s): %d chapters, %d failed -> %s" % (vi, name, total, len(fails), out_path))


if __name__ == "__main__":
    main()
