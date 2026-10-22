# -*- coding: utf-8 -*-
"""逐段最优匹配：列出新章每一段在原著里最像的那一段，按相似度排序。

用法：python top_sim.py 原章.txt 新章.txt [最短字数，默认 10]
"""
import sys, difflib, statistics


def load(p):
    return [l.strip() for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]


def main():
    if len(sys.argv) < 3:
        print("用法：python top_sim.py 原章.txt 新章.txt [最短字数，默认10]")
        return
    o, n = load(sys.argv[1]), load(sys.argv[2])
    floor = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    pairs = []
    for i, a in enumerate(n):
        if len(a) < floor:
            continue
        best = (0.0, -1)
        for j, b in enumerate(o):
            r = difflib.SequenceMatcher(None, a, b).ratio()
            if r > best[0]:
                best = (r, j)
        pairs.append((best[0], i, best[1]))
    pairs.sort(reverse=True)

    print("原著 %d 段 / 新章 %d 段（统计新段 ≥%d 字，共 %d 段）" % (len(o), len(n), floor, len(pairs)))
    print("=" * 84)
    for r, i, j in pairs[:20]:
        print("[%.0f%%] 新#%d · 原#%d" % (r * 100, i + 1, j + 1))
        print("   新: " + n[i])
        print("   原: " + o[j])
    print("=" * 84)
    print("平均最像度 %.1f%%" % (100 * statistics.mean([p[0] for p in pairs])))
    for th in (0.50, 0.40, 0.30, 0.25):
        print("≥%d%%: %d 段" % (th * 100, len([p for p in pairs if p[0] >= th])))


if __name__ == "__main__":
    main()
