# -*- coding: utf-8 -*-
"""节奏 + 结构相似度分析：不只比字面，还比"每一段在干什么"。

输出三部分：
1. 节奏指标：段长分布、单句成段比例、平均句长，分前半/后半对照
2. 逐段最优匹配：新章每段在同位置附近找到的最像的原文段（窗口 ±6 段）
3. 结构映射：按段落位置画一条"最像哪段"的对角线程度，越接近 1 说明结构越平行
"""
import re
import sys
import difflib

PUNCT = "，。！？；：、…—·“”‘’（）《》〈〉「」『』【】 \t\r\n\u3000"


def strip_punct(t):
    return "".join(c for c in t if c not in PUNCT)


def paras(path):
    t = open(path, encoding="utf-8-sig").read().split("\n")
    return [l.strip() for l in t[1:] if l.strip()]


def rhyme_stats(ps, tag):
    lens = [len(strip_punct(p)) for p in ps]
    short = sum(1 for x in lens if x <= 6)
    n = len(lens)
    avg = sum(lens) / n
    var = (sum((x - avg) ** 2 for x in lens) / n) ** 0.5
    print("  %-6s 段数 %3d | 平均段长 %5.1f 字 | 段长标准差 %5.1f | 单句成段 %d 段 (%.0f%%) | 最长段 %d 字"
          % (tag, n, avg, var, short, short / n * 100, max(lens)))


def main(old_path, new_path):
    op, np_ = paras(old_path), paras(new_path)
    on = [strip_punct(x) for x in op]
    nn = [strip_punct(x) for x in np_]

    print("=" * 78)
    print("一、节奏指标")
    print("=" * 78)
    rhyme_stats(op, "原著")
    rhyme_stats(np_, "新版")
    half_o, half_n = len(op) // 2, len(np_) // 2
    print("  --- 前半 ---")
    rhyme_stats(op[:half_o], "原著")
    rhyme_stats(np_[:half_n], "新版")
    print("  --- 后半 ---")
    rhyme_stats(op[half_o:], "原著")
    rhyme_stats(np_[half_n:], "新版")

    # 逐段最优匹配（窗口内）
    print("\n" + "=" * 78)
    print("二、逐段最优匹配（仅在原文同位置 ±6 段窗口内找，检验结构是否平行）")
    print("=" * 78)
    W = 6
    rows = []
    for i, q in enumerate(nn):
        if len(q) < 4:
            continue
        j0 = int(i / len(nn) * len(on))
        lo, hi = max(0, j0 - W), min(len(on), j0 + W + 1)
        best, bj = 0.0, -1
        for j in range(lo, hi):
            r = difflib.SequenceMatcher(None, q, on[j]).ratio()
            if r > best:
                best, bj = r, j
        rows.append((i, bj, best, np_[i], op[bj]))

    seg = len(rows) // 2
    front = [r for k, r in enumerate(rows) if k < seg]
    back = [r for k, r in enumerate(rows) if k >= seg]
    f = sum(r[2] for r in front) / len(front)
    b = sum(r[2] for r in back) / len(back)
    print("前半段平均最像度: %.1f%%   后半段: %.1f%%   整体: %.1f%%"
          % (f * 100, b * 100, (f * len(front) + b * len(back)) / len(rows) * 100))

    print("\n最像的 10 段（前半部分）：")
    for i, j, r, newp, oldp in sorted(front, key=lambda x: -x[2])[:10]:
        print("\n  [%.0f%%] 新#%d / 原#%d" % (r * 100, i + 1, j + 1))
        print("    新: %s" % (newp[:70] + ("…" if len(newp) > 70 else "")))
        print("    原: %s" % (oldp[:70] + ("…" if len(oldp) > 70 else "")))

    # 结构平行度：位置偏移
    print("\n" + "=" * 78)
    print("三、结构平行度（新第 i 段最像的原段位置 j，折算成百分比）")
    print("=" * 78)
    devs = []
    for i, j, r, _, _ in rows:
        if r < 0.3:
            continue
        pi = i / len(nn) * 100
        pj = j / len(on) * 100
        devs.append(abs(pi - pj))
    if devs:
        print("有效对位 %d 段，位置偏差中位数 %.1f%%，平均 %.1f%%（越小说明两章结构越平行）"
              % (len(devs), sorted(devs)[len(devs) // 2], sum(devs) / len(devs)))


if __name__ == "__main__":
    old = sys.argv[1]
    new = sys.argv[2]
    main(old, new)
