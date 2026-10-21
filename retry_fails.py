# -*- coding: utf-8 -*-
"""Retry chapters that failed during the per-volume scrape.
Reads every scrape_vol_*.log, finds 'FAIL <num> <url>' lines, re-fetches
those chapters, and patches the corresponding volume .txt (replacing the
'第N章 [抓取失败]' placeholder with real content).
"""
import os, re, json, time
import scrape_vol as sv   # reuse fetch_chapter / VOLUMES

WORKSPACE = os.path.dirname(os.path.abspath(__file__))


def patch_volume_txt(vol_name, num, title, body):
    path = os.path.join(WORKSPACE, vol_name + ".txt")
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    placeholder = "\n第%d章 [抓取失败]\n\n" % num
    if placeholder not in text:
        print("  WARN placeholder for ch%d not found in %s" % (num, vol_name))
        return False
    replacement = "\n%s\n\n%s\n\n" % (title, body)
    text = text.replace(placeholder, replacement, 1)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(text)
    return True


def main():
    log_dir = WORKSPACE
    fails = []  # (vol_index, num, url)
    for fn in sorted(os.listdir(log_dir)):
        m = re.match(r"scrape_vol_(\d+)\.log$", fn)
        if not m:
            continue
        vi = int(m.group(1))
        with open(os.path.join(log_dir, fn), encoding="utf-8") as f:
            for line in f:
                fm = re.match(r"FAIL (\d+) (\S+)", line.strip())
                if fm:
                    fails.append((vi, int(fm.group(1)), fm.group(2)))

    if not fails:
        print("No failed chapters to retry.")
        return

    # load titles from chapters.json for nicer headers
    with open(os.path.join(WORKSPACE, "chapters.json"), encoding="utf-8") as f:
        chs = json.load(f)
    title_by_url = {u: t for (_n, u, t) in chs}

    print("Found %d failed chapters to retry." % len(fails))
    still_bad = []
    for vi, num, url in fails:
        vol_name = sv.VOLUMES[vi][1]
        print("Retrying vol%d ch%d (%s) ..." % (vi, num, url))
        # a few extra attempts with longer backoff
        res = None
        for attempt in range(4):
            try:
                res = sv.fetch_chapter(url)
            except Exception as e:
                res = None
            if res and res[1]:
                break
            time.sleep(2 + attempt * 2)
        if not res or not res[1]:
            print("  STILL FAILED ch%d" % num)
            still_bad.append((vi, num, url))
            continue
        title, body = res
        # if the page title is empty, fall back to list title
        if not title:
            title = title_by_url.get(url, "第%d章" % num)
        if patch_volume_txt(vol_name, num, title, body):
            print("  OK patched ch%d (%d chars)" % (num, len(body)))
        else:
            still_bad.append((vi, num, url))

    if still_bad:
        print("\n%d chapters still failed after retry:" % len(still_bad))
        for vi, num, url in still_bad:
            print("  vol%d ch%d %s" % (vi, num, url))
    else:
        print("\nAll failed chapters recovered.")


if __name__ == "__main__":
    main()
