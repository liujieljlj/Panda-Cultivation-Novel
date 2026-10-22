# -*- coding: utf-8 -*-
"""深度雷同扫描：不只看"完全相同"，还要找出"改写后的近似雷同"。

做法：
1. 段落级：新章每段 vs 原著每段，取最高相似度，列出 >= 阈值 的配对
2. 句子级：按句读切分后逐句比对，列出 >= 阈值 的近似句
3. 词块级：找出连续 8~12 字的共同片段（比纯 n-gram 更能看清是哪句话像）
"""
import re
import sys
import difflib

PUNCT = "，。！？；：、…—·“”‘’（）《》〈〉「」『』 \t\r\n\u3000"


def strip_punct(t):
    return "".join(c for c in t if c not in PUNCT)


def load_paras(path):
    t = open(path, encoding="utf-8-sig").read()
    lines = t.split("\n")
    return [l.strip() for l in lines[1:] if l.strip()]


def load_sents(path):
    t = open(path, encoding="utf-8-sig").read()
    body = "\n".join(t.split("\n")[1:])
    out = []
    for seg in re.split(r"(?<=[。！？])", body.replace("\n", "")):
        s = seg.strip()
        if len(strip_punct(s)) >= 6:
            out.append(s)
    return out


def main(old_path, new_path, thr=0.45):
    op, np_ = load_paras(old_path), load_paras(new_path)
    o_norm = [strip_punct(x) for x in op]

    print("=" * 70)
    print("段落级近似比对（阈值 %.2f）" % thr)
    print("=" * 70)
    hits = []
    for i, para in enumerate(np_):
        q = strip_punct(para)
        if len(q) < 6:
            continue
        best, bj = 0.0, -1
        for j, cand in enumerate(o_norm):
            if len(cand) < 6:
                continue
            r = difflib.SequenceMatcher(None, q, cand).ratio()
            if r > best:
                best, bj = r, j
        if best >= thr:
            hits.append((best, i, bj, para, op[bj]))
    hits.sort(reverse=True)
    for r, i, j, new, old in hits:
        print("\n[相似度 %.0f%%] 新章第%d段" % (r * 100, i + 1))
        print("  新: %s" % (new[:110] + ("…" if len(new) > 110 else "")))
        print("  原: %s" % (old[:110] + ("…" if len(old) > 110 else "")))
    print("\n段落级命中: %d / %d 段" % (len(hits), len(np_)))

    # ---------- 句子级 ----------
    os_, ns_ = load_sents(old_path), load_sents(new_path)
    os_n = [strip_punct(x) for x in os_]
    print("\n" + "=" * 70)
    print("句子级近似比对（阈值 %.2f）" % thr)
    print("=" * 70)
    shits = []
    for s in ns_:
        q = strip_punct(s)
        best, bo = 0.0, ""
        for cand, cn in zip(os_, os_n):
            r = difflib.SequenceMatcher(None, q, cn).ratio()
            if r > best:
                best, bo = r, cand
        if best >= thr:
            shits.append((best, s, bo))
    shits.sort(reverse=True)
    for r, new, old in shits:
        print("\n[%.0f%%] 新: %s" % (r * 100, new))
        print("       原: %s" % old)
    print("\n句子级命中: %d / %d 句" % (len(shits), len(ns_)))

    # ---------- 8~12 字共同片段 ----------
    o_all = strip_punct("".join(op))
    n_all = strip_punct("".join(np_))
    print("\n" + "=" * 70)
    print("连续 8 字以上共同片段（去标点口径）")
    print("=" * 70)
    for k in (8, 10, 12):
        co = set(o_all[i:i + k] for i in range(len(o_all) - k + 1))
        segs = []
        i = 0
        while i <= len(n_all) - k:
            if n_all[i:i + k] in co:
                j = i + k
                while j < len(n_all) and (j - k + 1) >= 0 and n_all[j - k + 1:j + 1] in co:
                    j += 1
                segs.append(n_all[i:j])
                i = j
            else:
                i += 1
        print("\n  %d 字窗口命中片段 %d 处:" % (k, len(segs)))
        for s in segs:
            print("    [%d字] %s" % (len(s), s))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python 脚本/deep_scan.py <原著章.txt> <新章.txt>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
