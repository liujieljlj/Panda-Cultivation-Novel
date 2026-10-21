# -*- coding: utf-8 -*-
"""对比"熊猫版"章节与原著的重复度。

指标：
1. 字符级 SequenceMatcher 相似度（含与不含标点两种口径）
2. 最长公共子串
3. n-gram 重合率（n=6 / 10 / 15），用于近似"连续抄袭片段"判定
4. 长句重复：长度 >= 8 字且完全相同的句子
"""
import re
import sys
import difflib
from collections import Counter

PUNCT = "，。！？；：、…—·“”‘’（）《》 \t\r\n\u3000"


def load(path):
    t = open(path, encoding="utf-8-sig").read()
    lines = [l.strip() for l in t.split("\n")]
    # 第一行是章节标题，正文从标题后开始
    body = "\n".join(lines[1:]) if lines else t
    return body


def norm(t, keep_punct=False):
    t = t.replace("\u3000", " ")
    if keep_punct:
        return re.sub(r"\s+", "", t)
    return "".join(c for c in t if c not in PUNCT)


def ngrams(s, n):
    if len(s) < n:
        return Counter()
    return Counter(s[i:i + n] for i in range(len(s) - n + 1))


def overlap_ratio(a, b, n):
    """新文本中有多少比例的 n-gram 在原文本里出现过"""
    ca, cb = ngrams(a, n), ngrams(b, n)
    if not ca:
        return 0.0, 0
    hit = sum(min(v, cb.get(k, 0)) for k, v in ca.items())
    total = sum(ca.values())
    return hit / total, hit


def longest_common(a, b):
    m = difflib.SequenceMatcher(None, a, b, autojunk=False)
    best = m.find_longest_match(0, len(a), 0, len(b))
    return best.size, a[best.a:best.a + best.size]


def sentences(t):
    parts = re.split(r"[。！？\n]", t)
    return [p.strip() for p in parts if len(p.strip()) >= 8]


def main(old_path, new_path):
    old_raw, new_raw = load(old_path), load(new_path)
    o_p, n_p = norm(old_raw, True), norm(new_raw, True)
    o, n = norm(old_raw), norm(new_raw)

    print("=" * 62)
    print("原文正文字数（含标点）: %d ｜ 去标点: %d" % (len(o_p), len(o)))
    print("新版正文字数（含标点）: %d ｜ 去标点: %d" % (len(n_p), len(n)))
    print("=" * 62)

    # 1 整体相似度
    r_p = difflib.SequenceMatcher(None, o_p, n_p, autojunk=False).ratio()
    r = difflib.SequenceMatcher(None, o, n, autojunk=False).ratio()
    print("\n[1] 整体相似度 SequenceMatcher")
    print("    含标点: %.2f%%" % (r_p * 100))
    print("    去标点: %.2f%%" % (r * 100))

    # 2 最长公共子串
    size, frag = longest_common(o, n)
    print("\n[2] 最长连续相同片段: %d 字" % size)
    print("    内容: 「%s」" % frag)

    # 3 n-gram
    print("\n[3] 连续片段重合率（新章中 n 字连续片段能在原文找到的比例）")
    for k in (6, 10, 15):
        ratio, hit = overlap_ratio(n, o, k)
        print("    %2d-gram: %6.2f%%  (命中 %d / 共 %d)"
              % (k, ratio * 100, hit, sum(ngrams(n, k).values())))

    # 4 长句重复
    so = set(sentences(old_raw))
    sn = sentences(new_raw)
    dup = [s for s in sn if s in so]
    print("\n[4] 长句完全重复（>=8 字）")
    print("    新章长句 %d 句，其中与原文完全相同 %d 句（%.1f%%）"
          % (len(sn), len(dup), len(dup) / max(len(sn), 1) * 100))
    for s in dup[:15]:
        print("      · %s" % s)
    if len(dup) > 15:
        print("      ... 另 %d 句" % (len(dup) - 15))


if __name__ == "__main__":
    old = sys.argv[1] if len(sys.argv) > 1 else "第1章 一条蛇的日常.txt"
    new = sys.argv[2] if len(sys.argv) > 2 else "熊猫版_正文/第001章 一头熊猫的日常.txt"
    main(old, new)
