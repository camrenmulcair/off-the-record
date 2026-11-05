"""Rebuild index.html from src/issueN.html and issues.json (newest first).
Usage: python3 tools/build_site.py"""
import re, html
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'src'); OUT=ROOT
BASE='https://camrenmulcair.github.io/off-the-record/'
issues=[(i['n'],i['week']) for i in json.load(open(os.path.join(ROOT,'issues.json')))]
def content(n):
    s=open(f'{SRC}/issue{n}.html').read()
    c='<div class="brk">'+s.split('<div class="brk">',1)[1].split('<div class="foot">')[0]
    c=re.sub(r'<div class="sec"( style="[^"]*")?>(.*?)</div>',lambda m:f'<h3 class="sec"{m.group(1) or ""}>{m.group(2)}</h3>',c)
    c=c.replace('<div class="story">','<div class="story reveal">')
    c=re.sub(r'(<div class="story reveal">.*?)<h3>(.*?)</h3>',lambda m:m.group(1)+f'<h4 class="hl"><span>{m.group(2)}</span></h4>',c,flags=re.S)
    c=re.sub(r'<div class="brk">(\s*<span class="lab">BREAKING</span>.*?)<h3>(.*?)</h3>',lambda m:'<div class="brk reveal">'+m.group(1)+f'<h3 class="hl"><span>{m.group(2)}</span></h3>',c,flags=re.S)
    c=c.replace('<div class="score">','<div class="score reveal">')
    # fix margin inline styles on sec
    c=c.replace('margin-top:12px','margin-top:22px')
    return c
arts=[]
for n,d in issues:
    latest = n==issues[0][0]
    vid=''
    arts.append(f'''<article class="issue" id="issue-{n}" aria-labelledby="h-issue-{n}">
  <header class="ihead"><h2 id="h-issue-{n}">Issue No. {n}</h2><span class="idate">Week of {d}</span></header>
  {vid}
  {content(n)}
  <p class="dl-pdf"><a href="issues/off-the-record-issue-{n}.pdf">Download Issue {n} as a PDF</a></p>
</article>''')
nav=''.join(f'<a href="#issue-{n}">Issue {n}</a>' for n,_ in issues)
LOGO='<svg class="logo" width="52" height="52" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><rect x="4" y="4" width="92" height="92" rx="20" fill="#fff" stroke="#111" stroke-width="4"/><rect x="16" y="22" width="56" height="13" rx="1.5" fill="#111"/><rect x="16" y="41" width="68" height="18" rx="1.5" fill="#e5384f"/><text x="22" y="55" font-family="IBM Plex Mono, monospace" font-weight="700" font-size="14" fill="#fff" letter-spacing="2">OTR</text><rect x="16" y="65" width="46" height="13" rx="1.5" fill="#111"/></svg>'
page=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Off the Record · What your feed won't tell you</title>
<meta name="description" content="Off the Record: a weekly newsletter by Camren. Every issue, newest first.">
<meta property="og:type" content="website">
<meta property="og:title" content="Off the Record · Issue No. {issues[0][0]}">
<meta property="og:description" content="What your feed won't tell you. Every issue, newest first.">
<meta property="og:url" content="{BASE}">
<meta property="og:image" content="{BASE}media/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Off the Record masthead with a red Not for Distribution stamp">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#eceef2">
<link rel="icon" href="media/icon.png">
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<a class="skip" href="#issue-{issues[0][0]}">Skip to the latest issue</a>
<div class="col">
<header class="mast" role="banner">
  {LOGO}
  <div class="box"><h1>Off the Record</h1><p class="tg">What your feed won't tell you</p></div>
  <p class="il">A weekly newsletter by Camren · Montreal</p>
  <div class="stamp" aria-hidden="true">NOT FOR DISTRIBUTION</div>
</header>
<nav class="jump" aria-label="Jump to an issue">{nav}</nav>
<main>
{chr(10).join(arts)}
</main>
<footer class="signoff">
  <p class="sig">— C.</p>
  <p class="burn">BURN AFTER READING</p>
</footer>
</div>
<script src="motion.js" defer></script>
</body>
</html>'''
open(f'{OUT}/index.html','w').write(page)
