"""Rebuild index.html from src/issueN.html + issues.json + sources.json + reactions.json.
Usage: python3 tools/build_site.py
"""
import json, os, re, html
from urllib.parse import quote
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://camrenmulcair.github.io/off-the-record/'
J = lambda f: json.load(open(os.path.join(ROOT, f)))
issues = J('issues.json')
sources = J('sources.json')
reactions = J('reactions.json')

SEC_FILTER = {'Breaking': 'breaking', 'Foreign Affairs': 'foreign', 'Domestic': 'domestic',
              'Markets': 'markets', 'Bread and Circuses': 'circus', 'Monetary Policy': 'markets', "Last Week's Call": 'calls'}

def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:40].strip('-')

def srcs_for(n, title):
    for k, v in sources.get(str(n), {}).items():
        if not k.startswith('__') and title.startswith(k):
            return v
    return None

SHARE_SVG = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def src_html(lst):
    if not lst:
        return ''
    li = ''.join(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a></li>' for t, u in lst)
    return f'<details class="sources"><summary>Sources · {len(lst)}</summary><ul>{li}</ul></details>'


WRITERS = []

def decorate_bc(el, title, n):
    kind = el.get('data-kind', 'sports')
    w = el.get('data-writer', 'Guest')
    if w not in WRITERS:
        WRITERS.append(w)
    W = html.escape(w)
    K = 'SPORTS' if kind == 'sports' else 'MEDIA'
    el['class'] = el.get('class', []) + ['sp' if kind == 'sports' else 'md']
    under = ('<div class="valance" aria-hidden="true"></div><div class="drape l" aria-hidden="true"></div><div class="drape r" aria-hidden="true"></div>'
             f'<div class="ctitle" aria-hidden="true"><b>Bread and Circuses</b><span>{K}</span></div>')
    if kind == 'sports':
        under += '<div class="turf" aria-hidden="true"></div><div class="beam a" aria-hidden="true"></div><div class="beam b" aria-hidden="true"></div>'
        top = (f'<div class="board" aria-hidden="true"><div class="top"><span>BREAD AND CIRCUSES : SPORTS</span><span><span class="dot">●</span> LIVE</span></div>'
               f'<div class="main"><span class="nm">{W}</span><span class="clk" data-clock>00:00</span></div></div>')
        t = f'BREAD AND CIRCUSES · SPORTS · ISSUE NO. {n} · GUEST WRITER: {W.upper()} · READ THE FULL PIECE ABOVE · BREAD AND CIRCUSES · SPORTS ·'
        bottom = (f'<div class="foot-space"></div><div class="l3" aria-hidden="true"><span class="nm">{W} · Guest correspondent</span>'
                  f'<span class="tk"><span>{t}</span></span></div>')
    else:
        under += '<div class="halftone" aria-hidden="true"></div>' + ''.join(
            f'<span class="flash" aria-hidden="true" style="{s}"></span>' for s in [
                'left:-30px;top:20px;animation-delay:2.3s', 'right:-20px;top:60px;animation-delay:2.55s',
                'left:40%;top:-40px;animation-delay:2.8s', 'right:30%;bottom:-20px;animation-delay:3s',
                'left:-20px;bottom:40px;animation-delay:3.25s'])
        top = f'<div class="marquee" aria-hidden="true"><i></i><i></i><i></i><b><small>STARRING</small>{W}</b><i></i><i></i><i></i></div>'
        cam = lambda flip, lens: ('<svg viewBox="0 0 40 50"><circle cx="20" cy="10" r="7" fill="#141416"/><rect x="10" y="18" width="20" height="32" rx="6" fill="#141416"/>'
                                  + ('<rect x="18" y="4" width="18" height="12" rx="3" fill="#333"/><circle cx="30" cy="10" r="4" fill="%s"/>' if not flip else
                                     '<rect x="2" y="6" width="18" height="12" rx="3" fill="#333"/><circle cx="8" cy="12" r="4" fill="%s"/>') % lens + '</svg>')
        bottom = ('<div class="foot-space"></div><div class="press" aria-hidden="true">'
                  + cam(False, '#fff') + cam(True, '#fff') + cam(False, '#fff') + cam(True, '#ff2d8a') + '</div>')
    el.insert(0, BeautifulSoup(under, 'html.parser'))
    el.select_one('.ftab').insert_after(BeautifulSoup(top, 'html.parser'))
    tools = el.select_one('.st-tools')
    tools.insert_after(BeautifulSoup(bottom, 'html.parser'))

calls_all = []
STORYCOUNT = {}

def issue_block(n, week, latest):
    raw = open(os.path.join(ROOT, 'src', f'issue{n}.html')).read()
    body = raw.split('<div class="page">', 1)[1]
    soup = BeautifulSoup(body, 'html.parser')
    for x in soup.select('.m2, .foot, .sig, .burn'):
        x.decompose()
    sec = 'Breaking'
    # walk top-level children in order
    for el in list(soup.children):
        if not getattr(el, 'name', None):
            continue
        cls = el.get('class', [])
        if 'sec' in cls:
            sec = el.get_text(strip=True)
            el.name = 'h3'
            el['data-f'] = SEC_FILTER.get(sec, 'other')
            if el.get('style'):
                el['style'] = el['style'].replace('margin-top:12px', 'margin-top:22px')
            continue
        if 'brk' in cls or 'story' in cls:
            f = 'breaking' if 'brk' in cls else SEC_FILTER.get(sec, 'other')
            h = el.find('h3')
            title = h.get_text(' ', strip=True)
            sid = f'i{n}-{slug(title)}'
            el['id'] = sid
            el['data-f'] = f
            STORYCOUNT[n] = STORYCOUNT.get(n, 0) + 1
            label = 'BREAKING' if f == 'breaking' else sec.upper()
            color = {'breaking': '#141416', 'foreign': '#d97706', 'domestic': '#e5384f', 'markets': '#8e3fa6', 'circus': '#0f8b8d'}.get(f, '#6b6e78')
            el.insert(0, BeautifulSoup(f'<span class="ftab" style="--tab:{color}" aria-hidden="true">FILE {STORYCOUNT[n]:02d}{'' if f=='breaking' else ' · '+html.escape(label)}</span>', 'html.parser'))
            el['class'] = cls + ['reveal']
            h.name = 'h3' if 'brk' in cls else 'h4'
            h['class'] = ['hl']
            inner = h.decode_contents()
            h.clear()
            h.append(BeautifulSoup(f'<span>{inner}</span>', 'html.parser'))
            tools = BeautifulSoup(
                f'<div class="st-tools">{src_html(srcs_for(n, title))}'
                f'<button class="share" type="button" data-id="{sid}" data-title="{html.escape(title)}" '
                f'aria-label="Share this story: {html.escape(title)}">{SHARE_SVG}<span>Share</span></button></div>',
                'html.parser')
            # wrap every text block so the redaction bar covers the whole story
            for t in el.select('.dek, .bl') + [x for x in el.find_all('p', recursive=False) if not x.get('class')]:
                inner_t = t.decode_contents()
                t.clear()
                t.append(BeautifulSoup(f'<span class="rd">{inner_t}</span>', 'html.parser'))
            el.append(tools)
            if 'bc' in cls:
                decorate_bc(el, title, n)
            continue
        if 'score' in cls:
            el['data-f'] = 'calls'
            el['class'] = cls + ['reveal']
            for r in el.select('.row'):
                r.append(BeautifulSoup('<span class="ci" aria-hidden="true">CALLED IT</span>', 'html.parser'))
                lab = r.find('b').get_text(strip=True)
                ok = '✓' in r.find(class_='ck').get_text() or True
                calls_all.append((n, lab, ok))
            cs = sources.get(str(n), {}).get('__calls')
            if cs:
                el.append(BeautifulSoup(f'<div class="st-tools">{src_html(cs)}</div>', 'html.parser'))
            continue
        # placeholder boxes (e.g. "Coming next week") belong to the calls section
        if el.name == 'div' and 'Coming next week' in el.get_text():
            el['data-f'] = 'calls'
    content = str(soup).replace('</div></body></html>', '')
    wa = 'https://wa.me/?text=' + quote(f'Re: Off the Record, Issue {n} — ')
    return f'''<article class="issue{' latest' if latest else ''}" id="issue-{n}" aria-labelledby="h-issue-{n}">
  <header class="ihead"><h2 id="h-issue-{n}">Issue No. {n}</h2><span class="idate">Week of {week}</span></header>
  <div class="iactions">
    <button class="listen" type="button" aria-pressed="false"><span aria-hidden="true">▶</span> Listen</button>
    <a class="reply" href="{wa}" target="_blank" rel="noopener">Reply on WhatsApp</a>
    <a class="pdf" href="issues/off-the-record-issue-{n}.pdf">PDF</a>
  </div>
  <div class="ibody">
  {content}
  </div>
  <button class="expand" type="button">Show the full issue</button>
</article>'''

arts = [issue_block(i['n'], i['week'], k == 0) for k, i in enumerate(issues)]

def breaking_title(n):
    soup = BeautifulSoup(open(os.path.join(ROOT, 'src', f'issue{n}.html')).read(), 'html.parser')
    h = soup.select_one('.brk h3')
    return h.get_text(' ', strip=True) if h else ''

import datetime
covers = ''
for i in issues[1:]:
    covers += (f'<a class="cov" href="#issue-{i["n"]}"><span class="t">Off the Record</span>'
               f'<span class="n">ISSUE NO. {i["n"]} · {i["week"].upper().replace(", 2026", "")}</span>'
               f'<span class="st" aria-hidden="true">NOT FOR DISTRIBUTION</span>'
               f'<span class="b"><span class="lab2">BREAKING</span><span class="h">{html.escape(breaking_title(i["n"]))}</span></span></a>')
try:
    nxt = datetime.datetime.strptime(issues[0]['week'], '%b %d, %Y') + datetime.timedelta(days=7)
    nxt_s = nxt.strftime('%b %-d').upper()
except Exception:
    nxt_s = 'NEXT WEEK'
covers += f'<div class="cov next" aria-hidden="true">ISSUE NO. {issues[0]["n"] + 1}<br>COMING {nxt_s}</div>'
back = f'''<section class="back" id="back" aria-labelledby="h-back">
  <div class="pin"><div class="bhead"><h2 id="h-back">Back issues</h2><p>Tap a cover to read it.</p></div>
  <div class="strip" id="strip">{covers}</div></div>
</section>'''
arts.insert(1, back)

# Prediction tracker
hits = sum(1 for c in calls_all if c[2]); total = len(calls_all)
pct = round(100 * hits / total) if total else 0
call_rows = ''.join(
    f'<li><span class="ck" aria-hidden="true">✓</span><span>{html.escape(lab)}</span>'
    f'<a href="#issue-{n}">Issue {n}</a></li>' for n, lab, ok in calls_all)
tracker = f'''<div class="drawer-bg" id="drawer-bg" hidden></div>
<aside class="drawer" id="calls" aria-labelledby="h-calls" aria-hidden="true">
  <button type="button" class="drawer-x" aria-label="Close">✕</button>
  <h2 id="h-calls">Called it</h2>
  <p class="sub">Every prediction that came true, newest first.</p>
  <ul class="calls">{call_rows}</ul>
</aside>'''

# Best reactions
rx = ''
for r in reactions:
    b = ''
    for m in r['msgs']:
        if m.get('me'):
            b += f'<div class="bub r"><span class="nm">{html.escape(m["from"])}</span>{html.escape(m["text"])}</div>'
        else:
            b += f'<div class="bub l"><span class="nm">{html.escape(m["from"])}</span>{html.escape(m["text"])}</div>'
    rx += f'<figure class="thread"><figcaption>After <a href="#issue-{r["after"]}">Issue {r["after"]}</a></figcaption>{b}</figure>'
reacts = f'''<section class="panel" id="reactions" aria-labelledby="h-rx">
  <h2 id="h-rx">Best reactions</h2>
  <p class="sub">Straight from the group chat.</p>
  <div class="rx-window" data-lenis-prevent tabindex="0" aria-label="Group chat reactions, scrollable">{rx}</div>
  {'<p class="rx-more">Scroll inside the box for more ↓</p>' if len(reactions) > 1 else ''}
</section>'''

nav = f'<a href="#issue-{issues[0]["n"]}">Latest</a><a href="#reactions">Reactions</a>' + \
      '<button type="button" class="calls-btn" aria-expanded="false" aria-controls="calls">Called it ✓</button><a href="#back">Back issues</a>'
filters = ''.join(f'<button type="button" class="fl" data-f="{k}" aria-pressed="{"true" if k=="all" else "false"}">{v}</button>'
                  for k, v in [('all', 'All'), ('breaking', 'Breaking'), ('foreign', 'Foreign Affairs'),
                               ('domestic', 'Domestic'), ('markets', 'Markets'), ('circus', 'Bread &amp; Circuses'), ('calls', "Last Week's Call")])
bcchips = ''.join([f'<button type="button" class="bcc" data-w="all" aria-pressed="true">Everyone</button>'] +
                  [f'<button type="button" class="bcc" data-w="{html.escape(w)}" aria-pressed="false">{html.escape(w)}</button>' for w in WRITERS] +
                  ['<button type="button" class="bcc" data-k="sports" aria-pressed="false">Sports only</button>',
                   '<button type="button" class="bcc" data-k="media" aria-pressed="false">Media only</button>'])
LOGO = '<svg class="logo" width="52" height="52" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><rect x="4" y="4" width="92" height="92" rx="20" fill="#fff" stroke="#111" stroke-width="4"/><rect x="16" y="22" width="56" height="13" rx="1.5" fill="#111"/><rect x="16" y="41" width="68" height="18" rx="1.5" fill="#e5384f"/><text x="22" y="55" font-family="IBM Plex Mono, monospace" font-weight="700" font-size="14" fill="#fff" letter-spacing="2">OTR</text><rect x="16" y="65" width="46" height="13" rx="1.5" fill="#111"/></svg>'
L = issues[0]['n']
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Off the Record · What your feed won't tell you</title>
<meta name="description" content="Off the Record: a weekly newsletter. Every issue, newest first.">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:title" content="Off the Record · Issue No. {L}">
<meta property="og:description" content="What your feed won't tell you. Every issue, newest first.">
<meta property="og:url" content="{BASE}">
<meta property="og:image" content="{BASE}media/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Off the Record masthead with a red Not for Distribution stamp">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#eceef2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0e0f12" media="(prefers-color-scheme: dark)">
<link rel="icon" href="media/icon.png">
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<a class="skip" href="#issue-{L}">Skip to the latest issue</a>
<section class="cover" id="cover" aria-label="Off the Record">
  <div class="pin">
    <header class="mast" id="folder">
      {LOGO}
      <div class="box"><h1>Off the Record</h1><p class="tg">What your feed won't tell you</p></div>
      <p class="il">A weekly newsletter · Montreal</p>
      <p class="il2">Latest: Issue No. {L} · Week of {issues[0]['week']}</p>
      <div class="stamp" id="cstamp" aria-hidden="true">NOT FOR DISTRIBUTION</div>
    </header>
    <p class="hint" id="hint" aria-hidden="true">SCROLL TO OPEN THE FILE ↓</p>
  </div>
</section>
<div class="col">
<nav class="jump" aria-label="Jump to a section">{nav}</nav>
{reacts}
<div class="controls">
  <div class="filters" role="group" aria-label="Show only one section">{filters}</div>
  <div class="bcf" role="group" aria-label="Bread and Circuses writers" hidden>{bcchips}</div>
  <label class="toggle"><input type="checkbox" id="showall"> <span>Show all issues</span><small>Off: latest issue plus the back-issue strip. On: every issue in full.</small></label>
</div>
<p class="sr-only" id="announce" aria-live="polite"></p>
<main>
{chr(10).join(arts)}
</main>
<footer class="signoff">
  <p class="sig">— C.</p>
  <p class="burn">BURN AFTER READING</p>
</footer>
</div>
{tracker}
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="vendor/lenis.min.js" defer></script>
<script src="vendor/gsap.min.js" defer></script>
<script src="vendor/ScrollTrigger.min.js" defer></script>
<script src="app.js" defer></script>
</body>
</html>'''
import hashlib
def ver(f):
    return hashlib.md5(open(os.path.join(ROOT, f), 'rb').read()).hexdigest()[:8]
for f in ['style.css', 'app.js', 'vendor/lenis.min.js', 'vendor/gsap.min.js', 'vendor/ScrollTrigger.min.js']:
    page = page.replace(f'"{f}"', f'"{f}?v={ver(f)}"')
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('built', len(arts), 'issues,', total, 'calls')
