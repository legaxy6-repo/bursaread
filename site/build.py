#!/usr/bin/env python3
"""Build the Daily Desk website: plain HTML pages that search engines can read.

Input:  site/data/editions/<date>.json   (Malaysia reads)
        site/data/reads/<area>-<date>.json (Global, US, China, Japan, Singapore, Europe)
        site/data/closes/<date>.json     (closing numbers)
        site/config.json                 (domain, newsletter form action)
Output: docs/  (GitHub Pages can serve this folder)

Usage:  python3 site/build.py            # the real site, pretty URLs
        python3 site/build.py --preview  # explicit index.html links, root page as a fragment
"""
import datetime as dt
import html
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PREVIEW = "--preview" in sys.argv
OUT = os.path.join(os.path.dirname(HERE), "preview" if PREVIEW else "docs")
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
DOMAIN = (CONFIG.get("domain") or "").strip().strip("/")
SITE = CONFIG.get("site_name") or "Daily Desk"
TAGLINE = CONFIG.get("tagline") or ""
MYT = dt.timezone(dt.timedelta(hours=8))

# id, url slug, tab label, full name
AREAS = [
    ("gl", "global", "Global", "Global"),
    ("my", "malaysia", "Malaysia", "Malaysia"),
    ("us", "us", "US", "United States"),
    ("cn", "china", "China", "China & Hong Kong"),
    ("jp", "japan", "Japan", "Japan"),
    ("sg", "singapore", "Singapore", "Singapore"),
    ("eu", "europe", "Europe", "Europe & UK"),
]
AREA = {a[0]: a for a in AREAS}

DP = {"usdmyr": 4, "sgdmyr": 4, "cnymyr": 4, "audmyr": 4, "eurmyr": 4, "gbpmyr": 4, "jpymyr100": 4, "dxy": 2,
      "opr": 2, "myor": 2, "klibor3m": 2, "mgs3": 2, "mgs5": 2, "mgs10": 2, "ust2": 2, "ust10": 2, "spread_bp": 0,
      "klci": 2, "sp500": 2, "nasdaq": 2, "dow": 2, "brent": 2, "wti": 2, "cpo_3m": 0, "gold": 2, "fedfunds": 2,
      "shcomp": 2, "hsi": 2, "csi300": 2, "usdcny": 4, "lpr1y": 2, "nikkei": 2, "topix": 2, "usdjpy": 2, "jgb10": 2,
      "boj": 2, "sti": 2, "usdsgd": 4, "sora": 4, "stoxx600": 2, "dax": 2, "ftse": 2, "eurusd": 4, "gbpusd": 4,
      "bund10": 2, "gilt10": 2, "ecb": 2, "boe": 2}
MOVE = {"pct": {k: 0.5 for k in ("usdmyr", "sgdmyr", "cnymyr", "audmyr", "eurmyr", "gbpmyr", "jpymyr100", "dxy",
                                 "usdcny", "usdjpy", "usdsgd", "eurusd", "gbpusd")},
        "bp": {"mgs3": 5, "mgs5": 5, "mgs10": 5, "myor": 5, "ust2": 6, "ust10": 6, "jgb10": 5, "bund10": 6, "gilt10": 6}}
MOVE["pct"].update({k: 1 for k in ("klci", "sp500", "nasdaq", "dow", "shcomp", "hsi", "csi300", "nikkei", "topix",
                                   "sti", "stoxx600", "dax", "ftse")})
MOVE["pct"].update({"gold": 1.5, "cpo_3m": 2, "brent": 3, "wti": 3})

E = lambda s: html.escape("" if s is None else str(s), quote=True)


# ---------- data ----------
def load_dir(name):
    d = os.path.join(DATA, name)
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                j = json.load(open(os.path.join(d, f), encoding="utf-8"))
                if isinstance(j, dict) and isinstance(j.get("data"), dict) and "id" in j:
                    j = j["data"]
                if isinstance(j, dict):
                    out.append(j)
    return out


READS = {a[0]: {} for a in AREAS}
for e in load_dir("editions"):
    if isinstance(e.get("date"), str):
        READS["my"][e["date"]] = e
for r in load_dir("reads"):
    if isinstance(r.get("date"), str) and r.get("area") in READS:
        READS[r["area"]][r["date"]] = r
CLOSES = sorted((c for c in load_dir("closes") if isinstance(c.get("date"), str)), key=lambda c: c["date"])


# ---------- formatting ----------
def is_num(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    try:
        float(str(v))
        return str(v).strip() != ""
    except ValueError:
        return False


def fmt(v, dp):
    if not is_num(v):
        return None
    return f"{float(v):,.{dp}f}".replace("-", "−")


def sgn(v, dp, suffix=""):
    if not is_num(v):
        return None
    n = float(v)
    sign = "+" if n > 0 else ("−" if n < 0 else "")
    return f"{sign}{abs(n):,.{dp}f}{suffix}"


def s(v):
    return v if isinstance(v, str) else (str(v) if is_num(v) else "")


def arr(v):
    return v if isinstance(v, list) else []


def safe_url(u):
    return u if isinstance(u, str) and u.startswith(("https://", "http://")) else None


def day(d, long=False):
    try:
        x = dt.date.fromisoformat(d)
    except (TypeError, ValueError):
        return s(d)
    return x.strftime("%A %-d %B %Y") if long else x.strftime("%a %-d %b")


def myt(iso):
    try:
        t = dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=MYT)
    return t.astimezone(MYT).strftime("%H:%M")


# ---------- paths ----------
def href(prefix, target):
    """target is a site path like '' (home), 'us/', 'us/2026-11-27/', 'about/'."""
    if PREVIEW:
        return prefix + target + "index.html"
    return (prefix + target) or "./"


def area_dir(aid):
    return "" if aid == "gl" else AREA[aid][1] + "/"


def read_dir(aid, date):
    return AREA[aid][1] + "/" + date + "/"


# ---------- pieces ----------
def cite(it):
    if it.get("kind") == "inference":
        return '<span class="dd-cite"><span class="dd-tag dd-tag-inf">Desk inference</span></span>'
    src = E(s(it.get("source")) or "Source")
    u = safe_url(it.get("url"))
    link = f'<a href="{E(u)}" target="_blank" rel="noopener">{src} ↗</a>' if u else f"<span>{src} (link missing)</span>"
    return f'<span class="dd-cite"><span class="dd-tag dd-tag-rep">Reported</span>{link}</span>'


def section(sid, eyebrow, title, inner, cls="dd-sec"):
    h = f"<h2>{E(title)}</h2>" if title else ""
    return f'<section class="{cls}" id="{E(sid)}"><p class="dd-eyebrow">{E(eyebrow)}</p>{h}{inner}</section>'


def moved(r):
    k = r.get("key")
    if r.get("flag") is True:
        return True
    if k in MOVE["pct"] and is_num(r.get("pct")):
        return abs(float(r["pct"])) >= MOVE["pct"][k]
    if k in MOVE["bp"] and is_num(r.get("chg_bp")):
        return abs(float(r["chg_bp"])) >= MOVE["bp"][k]
    return False


def board_row(r, idp):
    k = s(r.get("key"))
    dp = int(r["dp"]) if is_num(r.get("dp")) else DP.get(k, 2)
    unit = s(r.get("unit"))
    v = float(r["pct"]) if is_num(r.get("pct")) else float(r["chg"]) if is_num(r.get("chg")) else float(r["chg_bp"]) if is_num(r.get("chg_bp")) else 0
    d = "up" if v > 0 else "down" if v < 0 else "flat"
    lv = fmt(r.get("level"), dp)
    parts = []
    if is_num(r.get("chg_bp")):
        parts.append(sgn(r["chg_bp"], 0, "bp"))
    else:
        if is_num(r.get("chg")):
            parts.append(sgn(r["chg"], dp))
        if is_num(r.get("pct")):
            parts.append(sgn(r["pct"], 2, "%"))
    arrow = "▲ " if d == "up" else "▼ " if d == "down" else ""
    chg = arrow + " · ".join(parts) if parts else ("not confirmed" if lv is None else "no change given")
    flag = '<span class="dd-moved" title="Passed the desk\'s move filter">moved</span>' if moved(r) else ""
    u = safe_url(r.get("url"))
    src = E(s(r.get("source")) or "source not given")
    src_html = f'<a href="{E(u)}" target="_blank" rel="noopener">{src}</a>' if u else src
    as_of = (E(s(r.get("as_of"))) + " · ") if s(r.get("as_of")) else ""
    rid = E(idp + "".join(ch for ch in k if ch.isalnum() or ch in "_-"))
    return (f'<div class="dd-row" id="{rid}" data-dir="{d}"><div class="dd-r-label">{E(s(r.get("label")) or k)}{flag}</div>'
            f'<div class="dd-r-level">{E(lv + unit) if lv is not None else "—"}</div><div class="dd-r-chg">{E(chg)}</div>'
            f'<div class="dd-r-meta">{as_of}{src_html}</div><div class="dd-r-spark"></div></div>')


def board_foot(note, gaps):
    out = ""
    if s(note):
        out += f'<p><span class="dd-tag dd-tag-inf">Desk inference</span> {E(note)}</p>'
    g = [s(x) for x in arr(gaps) if s(x)]
    if g:
        out += f'<p class="dd-gaps">Left blank (not confirmed): {E("; ".join(g))}</p>'
    return f'<div class="dd-board-foot">{out}</div>' if out else ""


def points(items, prefix, on_global=False):
    out = ""
    for p in arr(items):
        if not isinstance(p, dict) or not s(p.get("text")):
            continue
        c = cite(p)
        pa = s(p.get("area")).lower()
        if on_global and pa in AREA and pa != "gl":
            chip = f'<a class="dd-area-chip" href="{E(href(prefix, area_dir(pa)))}">{E(AREA[pa][2])} read →</a>'
            c = c.replace('<span class="dd-cite">', '<span class="dd-cite">' + chip, 1)
        cls = ' class="dd-inf"' if p.get("kind") == "inference" else ""
        out += f"<li{cls}><p>{E(p['text'])}</p>{c}</li>"
    return f'<ul class="dd-points">{out}</ul>' if out else ""


def cal_list(items):
    out = ""
    for c in arr(items):
        if not isinstance(c, dict) or not s(c.get("event")):
            continue
        u = safe_url(c.get("url"))
        ev = f'<a class="dd-cal-event" href="{E(u)}" target="_blank" rel="noopener">{E(c["event"])}</a>' if u else f'<span class="dd-cal-event">{E(c["event"])}</span>'
        why = f'<span class="dd-cal-why">{E(c.get("why"))}</span>' if s(c.get("why")) else ""
        out += (f'<li><span class="dd-cal-time">{E(c.get("time_myt"))}</span><span class="dd-region">{E(s(c.get("region")) or "—")}</span>'
                f'<div class="dd-cal-body">{ev}{why}</div></li>')
    return f'<ul class="dd-cal">{out}</ul>' if out else ""


def sources(rd):
    src = [x for x in arr(rd.get("sources")) if isinstance(x, dict)]
    if not src:
        return ""
    lis = ""
    for x in src:
        meta = " · ".join(v for v in (s(x.get("time_myt")), s(x.get("outlet"))) if v)
        u = safe_url(x.get("url"))
        t = E(s(x.get("title")) or s(x.get("url")))
        link = f'<a href="{E(u)}" target="_blank" rel="noopener">{t}</a>' if u else f"<span>{t}</span>"
        lis += f'<li><span class="dd-meta">{E(meta)}</span>{link}</li>'
    return f'<details class="dd-details" id="sources"><summary>Sources used in this read ({len(src)})</summary><ul class="dd-sources">{lis}</ul></details>'


def us_open(rd):
    u = rd.get("us_open")
    if not isinstance(u, dict):
        return ""
    when = s(u.get("as_of")) or ((myt(u.get("published_at")) or "") + " MYT")
    inner = points(u.get("drivers"), "")
    rows = [r for r in arr(u.get("board")) if isinstance(r, dict)]
    if rows:
        inner += ('<div class="dd-board"><div class="dd-bgroup"><h3>At the open, vs prior close</h3>'
                  + "".join(board_row(r, "uo-") for r in rows) + "</div></div>")
    if cal_list(u.get("watch")):
        inner += "<h3>Rest of the US session</h3>" + cal_list(u.get("watch"))
    if s(u.get("for_tomorrow")):
        inner += f'<h3>For Asia tomorrow</h3><p>{E(u["for_tomorrow"])}</p>{cite({"kind": "inference"})}'
    return section("us-open", "US open · " + when, s(u.get("setup")) or "How the US day is starting", inner, "dd-sec dd-late")


# ---------- read bodies ----------
def malaysia_body(ed, prefix):
    out = us_open(ed)
    ot = ed.get("one_thing") if isinstance(ed.get("one_thing"), dict) else {}
    steps = [x for x in arr(ot.get("steps")) if isinstance(x, dict)]
    lis = ""
    for i, st in enumerate(steps):
        so = s(st.get("node")).lower().startswith("so what")
        lis += (f'<li class="dd-step{" dd-sowhat" if so else ""}"><div class="dd-node"><span class="dd-num">{i + 1}</span>{E(st.get("node"))}</div>'
                f'<div class="dd-step-body"><p>{E(st.get("fact"))}</p>{cite(st)}</div></li>')
    sub = f"<h3>{E(ot.get('title'))}</h3>" if s(ot.get("title")) and s(ed.get("headline")) else ""
    out += section("one-thing", "The one thing", s(ed.get("headline")) or s(ot.get("title")) or "Today's main story",
                   sub + (f'<ol class="dd-chain">{lis}</ol>' if lis else '<p class="dd-note">No chain in this read.</p>'))
    groups = ""
    for key, title in (("fx", "Ringgit board · per unit unless stated"), ("rates", "Rates"), ("markets", "Markets")):
        rows = [r for r in arr(ed.get(key)) if isinstance(r, dict)]
        if rows:
            groups += f'<div class="dd-bgroup" id="board-{key}"><h3>{E(title)}</h3>' + "".join(board_row(r, "row-") for r in rows) + "</div>"
    if groups:
        out += section("rate-board", "The numbers", None, f'<div class="dd-board">{groups}{board_foot(ed.get("numbers_note"), ed.get("gaps"))}</div>' + history(ed))
    dk = ed.get("desk")
    if isinstance(dk, dict) and s(dk.get("question")):
        inner = f'<p class="dd-desk-q">{E(dk["question"])}</p>'
        if s(dk.get("explain")):
            inner += f"<p>{E(dk['explain'])}</p>{cite({'kind': 'inference'})}"
        chk = [s(c) for c in arr(dk.get("check")) if s(c)]
        if chk:
            inner += "<h3>Check before you answer</h3><ul class=\"dd-list\">" + "".join(f"<li>{E(c)}</li>" for c in chk) + "</ul>"
        out += section("at-the-desk", "At the desk", None, inner)
    cl = cal_list(ed.get("calendar"))
    out += section("calendar", "Today, in MYT", None, cl or '<p class="dd-note">Nothing scheduled that matters.</p>')
    for i, sec in enumerate(arr(ed.get("sections"))[:3]):
        if not isinstance(sec, dict):
            continue
        trig = f'<p class="dd-trigger">Why it\'s here: {E(sec.get("trigger"))}</p>' if s(sec.get("trigger")) else ""
        out += section("sec-" + (s(sec.get("key")) or str(i)), s(sec.get("title")) or "Also today", s(sec.get("headline")) or None,
                       trig + points(sec.get("points"), prefix))
    ln = ed.get("learn")
    if isinstance(ln, dict) and s(ln.get("concept")):
        inner = f"<h3>{E(ln['concept'])}</h3>" + (f"<p>{E(ln['body'])}</p>" if s(ln.get("body")) else "")
        if s(ln.get("question")):
            inner += f'<p class="dd-q">Test yourself: {E(ln["question"])}</p>'
            if s(ln.get("answer")):
                inner += f'<details><summary>Answer (think first)</summary><p>{E(ln["answer"])}</p></details>'
        out += section("learn", "Learn", None, f'<div class="dd-learn">{inner}</div>')
    return out + sources(ed)


STATUS = {"new": "New", "building": "Building", "fading": "Fading"}


def area_body(aid, rd, prefix):
    out = us_open(rd)
    pts = points(rd.get("points"), prefix, on_global=(aid == "gl"))
    out += section("worth-reading", "The day, worldwide" if aid == "gl" else "Worth reading", s(rd.get("headline")) or None,
                   pts or '<p class="dd-note">A quiet session. Nothing here is worth your time today.</p>')
    rows = [r for r in arr(rd.get("numbers")) if isinstance(r, dict)]
    if rows:
        out += section("area-numbers", "The numbers", None,
                       '<div class="dd-board"><div class="dd-bgroup"><h3>Closes and rates</h3>' + "".join(board_row(r, "an-") for r in rows)
                       + "</div>" + board_foot(rd.get("numbers_note"), rd.get("gaps")) + "</div>")
    devs = ""
    for d in arr(rd.get("developments")):
        if not isinstance(d, dict) or not s(d.get("title")):
            continue
        st = s(d.get("status")).lower()
        chip = f'<span class="dd-status" data-s="{E(st)}">{STATUS[st]}</span>' if st in STATUS else ""
        txt = f"<p>{E(d['text'])}</p>" if s(d.get("text")) else ""
        devs += f'<li><div class="dd-dev-head">{chip}<span class="dd-dev-title">{E(d["title"])}</span></div>{txt}{cite(d)}</li>'
    if devs:
        out += section("developments", "Developments to watch", None, f'<ul class="dd-devs">{devs}</ul>')
    cl = cal_list(rd.get("calendar"))
    if cl:
        out += section("area-calendar", "Coming up, in MYT", None, cl)
    if s(rd.get("for_malaysia")):
        out += section("for-malaysia", "What it means for Malaysia", None,
                       f'<div class="dd-for-my"><p>{E(rd["for_malaysia"])}</p>{cite({"kind": "inference"})}</div>')
    return out + sources(rd)


def history(ed):
    upto = s(ed.get("bursa_date")) or "9999"
    rows = [c for c in CLOSES if c["date"] <= upto][-12:][::-1]
    if not rows:
        return ""
    cols = [("klci", "KLCI", 2), ("usdmyr", "USD/MYR", 4), ("sgdmyr", "SGD/MYR", 4), ("mgs10", "MGS 10Y", 2),
            ("ust10", "UST 10Y", 2), ("spread_bp", "Spread bp", 0), ("brent", "Brent", 2), ("cpo_3m", "CPO", 0)]
    head = "<tr><th>Date</th>" + "".join(f"<th>{E(c[1])}</th>" for c in cols) + "</tr>"
    body = "".join("<tr><td>" + E(day(r["date"])) + "</td>" + "".join(f"<td>{E(fmt(r.get(c[0]), c[2]) or '—')}</td>" for c in cols) + "</tr>" for r in rows)
    return (f'<details class="dd-details" id="history"><summary>Recent closes as a table (ringgit: BNM 5pm middle rates)</summary>'
            f'<div class="dd-tablewrap"><table class="dd-table"><thead>{head}</thead><tbody>{body}</tbody></table></div></details>')


# ---------- page shell ----------
def covers_line(aid, rd):
    bits = []
    if aid not in ("my",):
        bits.append(f"<b>{E(AREA[aid][3])}</b>")
    if s(rd.get("covers")):
        bits.append(("<b>Covers</b> " if aid == "my" else "") + E(rd["covers"]))
    t = myt(rd.get("published_at"))
    if t:
        bits.append(f"Published {t} MYT")
    u = rd.get("us_open")
    if isinstance(u, dict) and myt(u.get("published_at")):
        bits.append(f"US open added {myt(u.get('published_at'))} MYT")
    return " · ".join(bits)


LIVE_HTML = """  <section class="dd-livecheck" id="live" aria-labelledby="live-title">
    <div class="dd-live-head">
      <p class="dd-eyebrow" id="live-title"><i class="dd-dot" id="live-dot" hidden></i>Live check <span>Interbank mid from Alpha Vantage. Bank board rates differ.</span></p>
      <div class="dd-live-actions"><button type="button" class="dd-btn" id="live-refresh" hidden disabled>Refresh</button></div>
    </div>
    <form class="dd-keyform" id="live-keyform">
      <label for="live-key">Your Alpha Vantage API key</label>
      <div class="dd-keyrow"><input class="dd-input" id="live-key" type="password" autocomplete="off" spellcheck="false" placeholder="Paste your key"><button class="dd-btn" type="submit">Save key</button></div>
      <p class="dd-live-status" id="live-keyhint">It stays in this browser only and is never sent anywhere except Alpha Vantage. Get a free key at <a href="https://www.alphavantage.co/support/#api-key" target="_blank" rel="noopener">alphavantage.co</a>.</p>
    </form>
    <div class="dd-tiles" id="live-tiles" hidden></div>
    <p class="dd-live-status" id="live-status" aria-live="polite"></p>
    <details class="dd-live-pick" id="live-pick" hidden><summary>Choose prices</summary><div class="dd-pick-grid" id="live-pick-grid"></div><button type="button" class="dd-linkbtn" id="live-forget">Remove the saved key from this browser</button></details>
  </section>
"""


def closes_json():
    out = {}
    for c in CLOSES:
        for k in ("usdmyr", "sgdmyr", "eurmyr", "gbpmyr", "audmyr", "cnymyr", "jpymyr100", "gold"):
            if is_num(c.get(k)):
                out[k] = {"date": c["date"], "v": float(c[k])}
    return json.dumps(out).replace("<", "\\u003c")


def shell(path, title, desc, body, active, kicker, h1, covers="", live=False):
    depth = path.count("/")
    prefix = "../" * depth
    canonical = (f"https://{DOMAIN}/" + path.replace("index.html", "")) if DOMAIN else ""
    tabs = "".join(
        f'<a href="{E(href(prefix, area_dir(a[0])))}"{" aria-current=\"page\"" if a[0] == active else ""}>{E(a[2])}</a>' for a in AREAS)
    nav_about = ' aria-current="page"' if active == "about" else ""
    nav_arch = ' aria-current="page"' if active == "archive" else ""
    head = (f"<title>{E(title)}</title>\n"
            f'<meta name="description" content="{E(desc)}">\n'
            + (f'<link rel="canonical" href="{E(canonical)}">\n' if canonical else "")
            + f'<meta property="og:title" content="{E(title)}">\n<meta property="og:description" content="{E(desc)}">\n'
            + '<meta property="og:type" content="article">\n'
            + (f'<meta property="og:url" content="{E(canonical)}">\n' if canonical else "")
            + '<meta name="theme-color" content="#121214">\n'
            + '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            + '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">\n'
            + f'<link rel="stylesheet" href="{prefix}assets/style.css">\n'
            + "<script>try{if(localStorage.getItem('dd-theme')==='light')document.documentElement.setAttribute('data-dd-theme','light')}catch(e){}</script>\n")
    content = f"""<header class="dd-bar" id="top">
  <div class="dd-wrapx dd-bar-row">
    <a class="dd-brand" href="{E(href(prefix, ''))}">{E(SITE)} <small>MY</small></a>
    <nav class="dd-bar-links" aria-label="Site">
      <a href="{E(href(prefix, 'archive/'))}"{nav_arch}>Archive</a>
      <a href="{E(href(prefix, 'about/'))}"{nav_about}>How it works</a>
      <a class="dd-cta" href="{E(href(prefix, ''))}#newsletter">Get the newsletter</a>
    </nav>
  </div>
  <div class="dd-wrapx"><nav class="dd-areas" aria-label="Areas">{tabs}</nav></div>
  <div class="dd-progress" aria-hidden="true"><span id="progress-bar"></span></div>
</header>
<div class="dd-wrap">
  <div class="dd-mast" id="masthead">
    <div class="dd-mast-top"><p class="dd-kicker">{E(kicker)}</p><button type="button" class="dd-theme" id="theme-toggle">Light mode</button></div>
    <h1>{E(h1)}</h1>
    {f'<p class="dd-covers">{covers}</p>' if covers else ''}
  </div>
{LIVE_HTML if live else ''}
  <main class="dd-main">
{body}
  </main>
  <footer class="dd-how" id="how">
    <h2>How this works</h2>
    <ul>
      <li>Every line tagged <b>Reported</b> links to the exact page that states it. Lines tagged <b>Desk inference</b> are the desk's own reasoning. A cause no reporter gave reads "no catalyst reported".</li>
      <li>Ringgit rates are Bank Negara Malaysia's official 5pm middle rates. A number that can't be confirmed is left blank.</li>
      <li>Analysis and education only. Nothing here is a buy or sell call. Times are Malaysia time (MYT, UTC+8).</li>
    </ul>
    <div class="dd-foot-base"><span>&copy; {dt.date.today().year} {E(SITE)}. Not investment advice.</span><a href="{E(href(prefix, 'about/'))}">Sources and corrections</a></div>
  </footer>
</div>
<script src="{prefix}assets/site.js"></script>
{(f'<script id="dd-closes" type="application/json">{closes_json()}</script><script src="{prefix}assets/live.js"></script>') if live else ''}
"""
    if PREVIEW and path == "index.html":
        return head + content  # the preview host wraps the root page itself
    return (f'<!doctype html>\n<html lang="en-MY" data-dd-theme="dark">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n{head}</head>\n<body>\n{content}</body>\n</html>\n')


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    PAGES.append(path)


PAGES = []


def newsletter_box():
    action = safe_url(CONFIG.get("newsletter_action")) or ""
    act = f' action="{E(action)}" method="post" target="_blank"' if action else ""
    note = "" if action else "Sign-ups open soon."
    return section("newsletter", "Newsletter", "The day's market read, in your inbox before 8am MYT",
                   f'<div class="dd-news"><p>One email each business day: the global summary, what it means for Malaysia, and one concept to learn. No buy or sell calls.</p>'
                   f'<form id="news-form"{act}><label for="news-email" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Email address</label>'
                   f'<input class="dd-input" id="news-email" name="email" type="email" autocomplete="email" placeholder="you@example.com" required>'
                   f'<button class="dd-btn" type="submit">Subscribe</button></form><p class="dd-live-status" id="news-note">{E(note)}</p></div>')


def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(OUT, "assets"))
    urls = []

    # area pages: latest at /<slug>/, every date at /<slug>/<date>/
    latest = {}
    for aid, slug, tab, name in AREAS:
        dates = sorted(READS[aid], reverse=True)
        if dates:
            latest[aid] = READS[aid][dates[0]]
        for i, date in enumerate(dates):
            rd = READS[aid][date]
            path = read_dir(aid, date) + "index.html"
            prefix = "../" * path.count("/")
            body = malaysia_body(rd, prefix) if aid == "my" else area_body(aid, rd, prefix)
            body += earlier(aid, dates, date, prefix)
            title = f"{name} market read, {day(date, True)} · {SITE}"
            write(path, shell(path, title, s(rd.get("headline")) or TAGLINE, body, aid, f"{name} read", day(date, True), covers_line(aid, rd)))
            urls.append(read_dir(aid, date))
        if aid != "gl":
            path = area_dir(aid) + "index.html"
            prefix = "../" * path.count("/")
            if dates:
                rd = latest[aid]
                body = (malaysia_body(rd, prefix) if aid == "my" else area_body(aid, rd, prefix)) + earlier(aid, dates, dates[0], prefix)
                write(path, shell(path, f"{name} market read · {SITE}", s(rd.get("headline")) or TAGLINE, body, aid,
                                  f"{name} read · latest", day(dates[0], True), covers_line(aid, rd), live=True))
            else:
                write(path, shell(path, f"{name} market read · {SITE}", TAGLINE, '<p class="dd-state">No read yet.</p>', aid, f"{name} read", name))
            urls.append(area_dir(aid))

    # home: the Global read plus every area's headline
    gl = latest.get("gl")
    today = ""
    for aid, slug, tab, name in AREAS[1:]:
        rd = latest.get(aid)
        if not rd:
            continue
        today += (f'<li><span class="dd-today-area">{E(name)}</span><p class="dd-today-head">{E(s(rd.get("headline")))}</p>'
                  f'<a class="dd-more" href="{E(href("", area_dir(aid)))}">Read →</a></li>')
    body = ""
    if gl:
        body += area_body("gl", gl, "")
    if today:
        body += section("by-area", "Today, by area", "Each market in one line", f'<ul class="dd-today">{today}</ul>')
    body += newsletter_box()
    write("index.html", shell("index.html", f"{SITE}: the world's markets, summarised for Malaysia",
                              s(gl.get("headline")) if gl else TAGLINE, body, "gl", "Global read · Malaysia time",
                              day(gl["date"], True) if gl else SITE, covers_line("gl", gl) if gl else E(TAGLINE), live=True))
    urls.insert(0, "")

    # archive
    blocks = ""
    for aid, slug, tab, name in AREAS:
        dates = sorted(READS[aid], reverse=True)
        if dates:
            blocks += (f"<section class=\"dd-sec\"><p class=\"dd-eyebrow\">{E(name)}</p><ul>"
                       + "".join(f'<li><a href="{E(href("../", read_dir(aid, d)))}">{E(day(d))}</a></li>' for d in dates) + "</ul></section>")
    write("archive/index.html", shell("archive/index.html", f"Archive · {SITE}", "Every daily read, by area and date.",
                                      f'<div class="dd-archive">{blocks or "<p class=dd-state>No reads yet.</p>"}</div>', "archive", "Archive", "Every read, by date"))
    urls.append("archive/")

    # about / methodology
    about = """<div class="dd-prose">
<p>Daily Desk summarises the world's markets each business day for readers new to finance, and explains what the moves mean for Malaysia: the ringgit, Malaysian rates and Bursa.</p>
<h3>Sources</h3>
<ul><li>Malaysia: Bernama, The Star, The Edge, NST, FMT, Business Today, Malay Mail, Bank Negara Malaysia, DOSM, Bursa Malaysia, the Securities Commission.</li>
<li>Abroad: AP, Reuters, CNBC, FT, WSJ, Bloomberg, Nikkei Asia, SCMP, The Business Times, and central banks and statistics offices.</li>
<li>Never: newsletters without a named reporter, AI-generated market sites, forecast sites, forums.</li></ul>
<h3>Reported or inference</h3>
<p>Every line tagged Reported links to the exact page that states it. Lines tagged Desk inference are the desk's own reasoning and are never presented as reporting. If no reporter gave a reason for a move, the read says "no catalyst reported".</p>
<h3>Numbers</h3>
<p>Ringgit rates are Bank Negara Malaysia's 5pm middle rates. Other figures carry their time and source. A number that can't be confirmed is left blank and listed under "Left blank". Market prices are shown as reported, not as a live feed.</p>
<h3>Corrections</h3>
<p>Errors are corrected in place, with a dated note in the read. Spot one? Use the contact on this page once it's live.</p>
<h3>Not advice</h3>
<p>Analysis and education only. Nothing on this site is a recommendation to buy or sell anything.</p>
</div>"""
    write("about/index.html", shell("about/index.html", f"How it works · {SITE}", "Sources, the reported-vs-inference rule, and corrections.",
                                    section("method", "How it works", "Sources, rules and corrections", about), "about", "How it works", "How Daily Desk works"))
    urls.append("about/")

    write("404.html", shell("404.html", f"Not found · {SITE}", TAGLINE,
                            f'<p class="dd-state">That page doesn\'t exist. <a href="{E(href("", ""))}">Go to today\'s read</a>.</p>', "", "Not found", "Page not found"))

    # robots, sitemap, CNAME
    if DOMAIN:
        sm = "".join(f"<url><loc>https://{DOMAIN}/{u}</loc></url>" for u in urls)
        open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
        open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: https://{DOMAIN}/sitemap.xml\n")
        open(os.path.join(OUT, "CNAME"), "w").write(DOMAIN + "\n")
    else:
        open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nAllow: /\n")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    print(f"Built {len(PAGES)} pages into {OUT}" + ("" if DOMAIN else " (no domain set: sitemap and CNAME skipped)"))


def earlier(aid, dates, current, prefix):
    others = [d for d in dates if d != current][:10]
    if not others:
        return ""
    links = "".join(f'<li><a href="{E(href(prefix, read_dir(aid, d)))}">{E(day(d))}</a></li>' for d in others)
    return f'<section class="dd-sec dd-archive" id="earlier"><p class="dd-eyebrow">Earlier {E(AREA[aid][3])} reads</p><ul>{links}</ul></section>'


if __name__ == "__main__":
    build()
