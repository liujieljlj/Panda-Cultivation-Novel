# -*- coding: utf-8 -*-
"""Build the full chapter list for zhiguge.com and verify volume boundaries."""
import urllib.request, re, json, time, os

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
BOOK_URL = "https://www.zhiguge.com/4nz3/l438o9/"
BASE = "https://www.zhiguge.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def get(u, tries=4):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                u, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
                            "Referer": BOOK_URL})
            return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.0)
    return None


def main():
    html = get(BOOK_URL)
    if not html:
        print("FAILED to fetch book page")
        return
    # robust: grab each <a href=.../l438o9/XX.html>...</a> block, strip tags,
    # then look for 第N章 in the inner text (handles nested <span> etc.)
    pat = re.compile(
        r'<a\s+href="([^"]*?/4nz3/l438o9/([A-Za-z0-9]+\.html))"[^>]*>(.*?)</a>',
        re.I | re.S)
    seen = {}
    for m in pat.finditer(html):
        rel, cid, inner = m.group(1), m.group(2), m.group(3)
        txt = re.sub(r'<[^>]+>', '', inner)
        cm = re.search(r'第(\d+)\s*章', txt)
        if not cm:
            continue
        num = int(cm.group(1))
        url = rel if rel.startswith("http") else BASE + rel
        if num not in seen:
            seen[num] = [num, url, txt.strip()]
    chapters = sorted(seen.values(), key=lambda x: x[0])
    print("total chapters:", len(chapters))
    print("first:", chapters[0])
    print("last:", chapters[-1])
    nums = [c[0] for c in chapters]
    missing = [n for n in range(1, max(nums) + 1) if n not in seen]
    print("missing in 1..max:", missing[:20], "...count", len(missing))

    VOLUMES = [
        (1, "第一卷 龙蛇起陆"), (51, "第二卷 血海飘摇"),
        (115, "第三卷 南沧风起"), (189, "第四卷 玄皇镇世"),
        (314, "第五卷 朝风古界"), (457, "第六卷 离乱之主"),
        (551, "第七卷 天尊无量"), (675, "第八卷 登阶化仙"),
    ]
    print("--- volume boundary check ---")
    for start, name in VOLUMES:
        print(f"  {name}: 第{start}章 -> {'OK' if start in seen else 'MISSING'}")

    out = os.path.join(WORKSPACE, "chapters.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False)
    print("saved ->", out)


if __name__ == "__main__":
    main()
