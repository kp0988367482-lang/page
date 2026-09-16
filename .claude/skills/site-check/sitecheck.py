#!/usr/bin/env python3
"""全站一致性稽核與自我修復。

  python3 sitecheck.py          只檢查，有問題 exit 1
  python3 sitecheck.py --fix    先自動修好能修的，再檢查剩下的

能自動修的，都是「答案唯一、改了不會有第二種解釋」的項目。
牽涉商業判斷或版面外觀的，一律只回報，不代做決定——清單見 SKILL.md。
"""
import re
import sys
import glob
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
ROOT = os.path.normpath(ROOT)
CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.conf")

# 這些外連不需要 target="_blank"（資源檔或 iframe 內部用）
TARGET_EXEMPT = ("fonts.googleapis", "fonts.gstatic", "w3.org", "assets.calendly")

# success.html 是付款完成頁，用的是 LINE 群組連結而非官方帳號私訊。
# 這是刻意的：commit 48415f0「open chat is post-purchase only」。
# 群組連結長 line.me/ti/g/…，不可被官方帳號取代。
LINE_GROUP_RE = re.compile(r"line\.me/ti/g/")


def load_conf():
    conf = {}
    with open(CONF, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            conf[k.strip()] = v.strip()
    return conf


def pages():
    return sorted(glob.glob(os.path.join(ROOT, "*.html")))


def name(p):
    return os.path.basename(p)


# ---------------------------------------------------------------- 修


def fix_paypal(s, conf):
    """PayPal 長網址 → 短網址。同帳號同金額，純寫法。"""
    user = conf.get("PAYPAL_USER", "")
    if not user:
        return s, 0
    new, n = re.subn(
        r"https://www\.paypal\.com/paypalme/" + re.escape(user),
        "https://paypal.me/" + user,
        s,
    )
    return new, n


def fix_line(s, conf):
    """所有 LINE 個人/舊帳號連結 → 官方帳號。群組連結不動。"""
    canon = conf.get("LINE_URL", "")
    if not canon:
        return s, 0
    n = 0

    def sub(m):
        nonlocal n
        url = m.group(0)
        if LINE_GROUP_RE.search(url) or url == canon:
            return url
        n += 1
        return canon

    return re.sub(r"https://line\.me/[^\"'\s>]+", sub, s), n


def fix_calendly(s, conf):
    """Calendly 舊帳號 → 現行帳號。已帶查詢參數的連結保留參數。"""
    canon = conf.get("CALENDLY_URL", "")
    if not canon:
        return s, 0
    canon_user = canon.split("calendly.com/", 1)[-1].split("?")[0]
    n = 0

    def sub(m):
        nonlocal n
        rest = m.group(1)          # calendly.com/ 之後的部分
        path, sep, query = rest.partition("?")
        if path.rstrip("/") == canon_user.rstrip("/"):
            return m.group(0)
        n += 1
        return "https://calendly.com/" + canon_user + sep + query

    return re.sub(r"https://calendly\.com/([^\"'\s>]*)", sub, s), n


def fix_target(s, conf):
    """外部連結補 target="_blank" rel="noopener"。"""
    n = 0

    def sub(m):
        nonlocal n
        tag = m.group(0)
        if "target=" in tag:
            return tag
        href = re.search(r'href="(https?://[^"]+)"', tag)
        if not href or any(x in href.group(1) for x in TARGET_EXEMPT):
            return tag
        n += 1
        return tag[:-1].rstrip() + ' target="_blank" rel="noopener">'

    return re.sub(r"<a\s[^>]*>", sub, s), n


def fix_lang(s, conf):
    """<html> 補 lang 屬性。"""
    lang = conf.get("HTML_LANG", "")
    if not lang or re.search(r"<html[^>]*\slang=", s, re.I):
        return s, 0
    return re.sub(r"<html\b", '<html lang="%s"' % lang, s, count=1, flags=re.I), 1


def fix_viewport(s, conf):
    """補 viewport meta，否則手機版整個壞掉。"""
    if re.search(r'name="viewport"', s, re.I):
        return s, 0
    tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    m = re.search(r"[ \t]*<meta[^>]*charset[^>]*>\n", s, re.I)
    if not m:
        m = re.search(r"[ \t]*<head[^>]*>\n", s, re.I)
    if not m:
        return s, 0
    indent = re.match(r"[ \t]*", m.group(0)).group(0)
    return s[: m.end()] + indent + tag + "\n" + s[m.end():], 1


FIXERS = [
    ("PayPal 網址改用短網址", fix_paypal),
    ("LINE 連結改為官方帳號", fix_line),
    ("Calendly 改為現行帳號", fix_calendly),
    ('外部連結補 target="_blank"', fix_target),
    ("<html> 補 lang", fix_lang),
    ("補 viewport meta", fix_viewport),
]


def run_fix(conf):
    tally = {}
    touched = set()
    for p in pages():
        with open(p, encoding="utf-8") as fh:
            orig = s = fh.read()
        for label, fn in FIXERS:
            s, n = fn(s, conf)
            if n:
                tally[label] = tally.get(label, 0) + n
        if s != orig:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(s)
            touched.add(name(p))
    if not tally:
        print("自動修復：沒有可修的項目。")
        return
    print("自動修復：")
    for label, n in tally.items():
        print("  %-28s %d 處" % (label, n))
    print("  影響 %d 個檔案：%s" % (len(touched), " ".join(sorted(touched))))
    print()


# ---------------------------------------------------------------- 查

GOOGLE_FAMILIES = (
    "Noto Serif TC", "Noto Sans KR", "DM Serif Display", "Outfit", "Space Mono",
)


def check(conf):
    findings = []

    def add(title, lines, hint=""):
        if lines:
            findings.append((title, lines, hint))

    texts = {}
    for p in pages():
        with open(p, encoding="utf-8") as fh:
            texts[name(p)] = fh.read()

    # 1. PayPal 一律短網址
    add("PayPal 仍有長網址",
        ["%s: %s" % (f, "www.paypal.com/paypalme")
         for f, s in texts.items() if "paypal.com/paypalme" in s])

    # 2. 金額對應商品。永不自動修：$19 和 $79 是兩個商品，不是筆誤。
    add("$19（PDF 攻略）出現在非 arrival-* 頁",
        [f for f, s in texts.items()
         if re.search(r"paypal[^\"]*/19", s) and not f.startswith("arrival-")],
        "這代表該頁掛錯商品，屬於商業決策，腳本不代選")
    add("$79（1:1 諮詢）出現在 arrival-* 頁",
        [f for f, s in texts.items()
         if re.search(r"paypal[^\"]*/79", s) and f.startswith("arrival-")],
        "同上，不自動修")

    # 3/4. LINE 與 Calendly：先看全站是否有多種寫法
    for label, pat, key, extra in (
        ("LINE", r"https://line\.me/[^\"'\s>]+", "LINE_URL", LINE_GROUP_RE),
        ("Calendly", r"https://calendly\.com/[^\"'?\s>]*", "CALENDLY_URL", None),
    ):
        seen = {}
        for f, s in texts.items():
            for u in re.findall(pat, s):
                if extra and extra.search(u):
                    continue          # 群組連結是另一種用途，不參與比對
                seen.setdefault(u, set()).add(f)
        canon = conf.get(key, "")
        if canon:
            bad = ["%s（%d 頁：%s）" % (u, len(fs), " ".join(sorted(fs)))
                   for u, fs in seen.items() if u.split("?")[0] != canon.split("?")[0]]
            add("%s 連結與正解不符" % label, bad,
                "正解 %s，來自 rules.conf。跑 --fix 可自動改齊" % canon)
        elif len(seen) > 1:
            add("%s 全站有 %d 種寫法，但 rules.conf 未指定正解" % (label, len(seen)),
                ["%s（%d 頁）" % (u, len(fs)) for u, fs in sorted(seen.items())],
                "填好 rules.conf 的 %s 之後跑 --fix，即可一次改齊" % key)

    # 5. CSS 用到的 Google 字型必須真的載進來（不強制各頁字型一致——
    #    index/success 用系統字體是刻意的設計，b2b 等頁沒韓文就不該載韓文字型）
    bad = []
    for f, s in texts.items():
        url = re.search(r"fonts\.googleapis\.com/css2\?([^\"']*)", s)
        loaded = url.group(1) if url else ""
        for fam in GOOGLE_FAMILIES:
            used = re.search(r"font-family:[^;}\"']*['\"]?" + re.escape(fam), s, re.I)
            if used and fam.replace(" ", "+") not in loaded:
                bad.append("%s：CSS 用了 %s，但沒載入" % (f, fam))
        if url and "display=swap" not in loaded:
            bad.append("%s：字型缺 display=swap（載入期間文字會消失）" % f)
    add("字型宣告與載入不一致", sorted(bad))

    # 6. HTML 基本標籤
    bad = []
    for f, s in texts.items():
        if not re.search(r"<html[^>]*\slang=", s, re.I):
            bad.append("%s：<html> 缺 lang" % f)
        if not re.search(r'name="viewport"', s, re.I):
            bad.append("%s：缺 viewport meta（手機版會壞）" % f)
        if not re.search(r"<title>", s, re.I):
            bad.append("%s：缺 <title>" % f)
        if not re.search(r'name="description"', s, re.I):
            bad.append("%s：缺 description meta" % f)
    add("HTML 基本標籤缺漏", sorted(bad),
        "description 需逐頁按內容撰寫，不套罐頭文案，因此不自動填")

    # 7. 外連應開新分頁
    bad = []
    for f, s in texts.items():
        for tag in re.findall(r"<a\s[^>]*>", s):
            href = re.search(r'href="(https?://[^"]+)"', tag)
            if not href or "target=" in tag:
                continue
            if any(x in href.group(1) for x in TARGET_EXEMPT):
                continue
            bad.append("%s：%s" % (f, href.group(1)[:70]))
    add('外部連結沒有 target="_blank"', sorted(bad))

    return findings


def main():
    conf = load_conf()
    if "--fix" in sys.argv:
        run_fix(conf)

    findings = check(conf)
    if not findings:
        print("✅ 全站一致性檢查通過（%d 個頁面）" % len(pages()))
        return 0

    for title, lines, hint in findings:
        print("\n[%s]" % title)
        for l in lines:
            print("  " + l)
        if hint:
            print("  → " + hint)
    print("\n%d 類問題待處理。" % len(findings))
    return 1


if __name__ == "__main__":
    sys.exit(main())
