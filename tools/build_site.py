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
              'Markets': 'markets', 'Monetary Policy': 'markets', "Last Week's Call": 'calls'}

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
    return f'<details class="sources"><summary>Sources</summary><ul>{li}</ul></details>'

calls_all = []

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
            el.append(tools)
            continue
        if 'score' in cls:
            el['data-f'] = 'calls'
            el['class'] = cls + ['reveal']
            for r in el.select('.row'):
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

# Prediction tracker
hits = sum(1 for c in calls_all if c[2]); total = len(calls_all)
pct = round(100 * hits / total) if total else 0
call_rows = ''.join(
    f'<li><span class="ck" aria-hidden="true">✓</span><span>{html.escape(lab)}</span>'
    f'<a href="#issue-{n}">Issue {n}</a></li>' for n, lab, ok in calls_all)
tracker = f'''<section class="panel" id="calls" aria-labelledby="h-calls">
  <h2 id="h-calls">My calls</h2>
  <p class="rec"><strong>{hits} / {total}</strong> called since Issue 1</p>
  <div class="bar" role="img" aria-label="{hits} of {total} calls right"><i style="width:{pct}%"></i></div>
  <ul class="calls">{call_rows}</ul>
</section>'''

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
  <div class="chatwall">{rx}</div>
</section>'''

nav = ''.join(f'<a href="#issue-{i["n"]}">Issue {i["n"]}</a>' for i in issues) + \
      '<a href="#calls">My calls</a><a href="#reactions">Reactions</a>'
filters = ''.join(f'<button type="button" class="fl" data-f="{k}" aria-pressed="{"true" if k=="all" else "false"}">{v}</button>'
                  for k, v in [('all', 'All'), ('breaking', 'Breaking'), ('foreign', 'Foreign Affairs'),
                               ('domestic', 'Domestic'), ('markets', 'Markets'), ('calls', "Last Week's Call")])
LOGO = '<svg class="logo" width="52" height="52" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><rect x="4" y="4" width="92" height="92" rx="20" fill="#fff" stroke="#111" stroke-width="4"/><rect x="16" y="22" width="56" height="13" rx="1.5" fill="#111"/><rect x="16" y="41" width="68" height="18" rx="1.5" fill="#e5384f"/><text x="22" y="55" font-family="IBM Plex Mono, monospace" font-weight="700" font-size="14" fill="#fff" letter-spacing="2">OTR</text><rect x="16" y="65" width="46" height="13" rx="1.5" fill="#111"/></svg>'
L = issues[0]['n']
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Off the Record · What your feed won't tell you</title>
<meta name="description" content="Off the Record: a weekly newsletter by Camren. Every issue, newest first.">
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
<div class="col">
<header class="mast">
  {LOGO}
  <div class="box"><h1>Off the Record</h1><p class="tg">What your feed won't tell you</p></div>
  <p class="il">A weekly newsletter by Camren · Montreal</p>
  <a class="record" href="#calls">Calls: <strong>{hits}/{total}</strong> ✓</a>
  <div class="stamp" aria-hidden="true">NOT FOR DISTRIBUTION</div>
</header>
<nav class="jump" aria-label="Jump to a section">{nav}</nav>
<div class="controls">
  <div class="filters" role="group" aria-label="Show only one section">{filters}</div>
  <label class="toggle"><input type="checkbox" id="compact"> <span>Compact archive</span><small>Show older issues as headlines only</small></label>
</div>
<p class="sr-only" id="announce" aria-live="polite"></p>
<main>
{chr(10).join(arts)}
{tracker}
{reacts}
</main>
<footer class="signoff">
  <p class="sig">— C.</p>
  <p class="burn">BURN AFTER READING</p>
</footer>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="app.js" defer></script>
</body>
</html>'''
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('built', len(arts), 'issues,', total, 'calls')
