"""Make the ~14 s vertical trailer (1080x1920 MP4) for one issue.
Usage: python3 tools/trailer.py N [out.mp4]
Needs playwright (pre-installed) and ffmpeg."""
import os, sys, subprocess, shutil, tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSCODE="\nconst $=q=>document.querySelector(q),$$=q=>[...document.querySelectorAll(q)];\nconst page=$('.page'),logo=$('.m2 .lg'),title=$('.m2 .box'),il=$('.m2 .il'),stamp=$('.stamp'),brk=$('.brk'),h=$('.brk h3'),end=$('#endc'),dc=$('#dcard'),dl=$('#dcard .lb'),D=dc?4.4:0,nc=$('#ncard'),N=nc?4.6:0,nis=$$('#ncard li'),nl=$('#ncard .lb');\nconst H=h.textContent, IL=il.textContent;\nconst rows=$$('.row');\nconst cl=(x)=>Math.max(0,Math.min(1,x)), seg=(t,a,b)=>cl((t-a)/(b-a));\nconst eo=x=>1-Math.pow(1-x,3), back=x=>{const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};\nconst rest=$$('.page > .sec, .page > .story, .page > .score, .page > .foot, .page > .chat, .page > .sig, .page > .burn').concat($$('.page > .brk').slice(1));\nbrk.style.minHeight=brk.offsetHeight+'px';\nconst maxScroll=page.offsetHeight-853+36;\nwindow.setT=function(t){\n  let a=eo(seg(t,0.1,0.6)); logo.style.opacity=a; logo.style.transform=`translateY(${(1-a)*20}px)`;\n  a=eo(seg(t,0.4,1.0)); title.style.opacity=a; title.style.transform=`translateY(${(1-a)*24}px)`;\n  let p=seg(t,1.2,1.5); stamp.style.opacity=p>0?1:0;\n  let sc=p<1?2.6-1.6*eo(p):1; let shake=(t>1.5&&t<1.75)?Math.sin(t*90)*3*(1.75-t)*4:0;\n  stamp.style.transform=`rotate(-9deg) scale(${sc}) translateX(${shake}px)`;\n  let n=Math.floor(IL.length*seg(t,1.7,2.3)); il.textContent=IL.slice(0,n)||'\xa0';\n  a=eo(seg(t,2.4,2.9)); brk.style.opacity=a; brk.style.transform=`translateX(${(1-a)*-40}px)`;\n  n=Math.floor(H.length*seg(t,2.8,4.4)); h.textContent=H.slice(0,n)+(t>2.8&&t<4.6&&Math.floor(t*4)%2?'▍':'');\n  $$('.brk .dek,.brk .bl').forEach(e=>e.style.opacity=eo(seg(t,4.4,4.9)));\n  let sp=seg(t,5.6,11.6); sp=sp<.5?2*sp*sp:1-Math.pow(-2*sp+2,2)/2;\n  page.style.transform=`translateY(${-sp*maxScroll}px)`;\n  rows.forEach((r,i)=>{const q=back(seg(t,10.6+i*0.35,10.95+i*0.35));const ck=r.querySelector('.ck');ck.style.transform=`scale(${q})`;r.style.opacity=0.25+0.75*cl(seg(t,10.5+i*0.35,10.8+i*0.35))});\n  rest.forEach(e=>e.style.opacity=eo(seg(t,4.8,5.5)));\n  if(nc){nc.style.opacity=eo(seg(t,12.2,12.5));let q0=seg(t,12.4,12.7);nl.style.opacity=q0>0?1:0;nl.style.transform=`rotate(-4deg) scale(${q0<1?2.6-1.6*eo(q0):1})`;nis.forEach((li,i)=>{const q=seg(t,12.8+i*0.42,13.15+i*0.42);li.style.opacity=cl(q*2);li.style.transform=`translateX(${(1-eo(q))*-60}px) scale(${0.9+0.1*back(q)})`})}\n  if(dc){dc.style.opacity=eo(seg(t,12.2+N,12.6+N));let q=seg(t,12.6+N,12.9+N);dl.style.opacity=q>0?1:0;dl.style.transform=`rotate(-4deg) scale(${q<1?2.6-1.6*eo(q):1})`;}\n  end.style.opacity=eo(seg(t,12.2+N+D,12.8+N+D));\n};\nsetT(0);\n"
n=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else f'/home/claude/off-the-record-issue-{n}-trailer.mp4'
s=open(os.path.join(ROOT,'src',f'issue{n}.html')).read()
s=s.replace('body{margin:0;background:#eceef2;padding:18px;width:480px;','body{margin:0;background:#eceef2;padding:0;width:480px;height:853px;overflow:hidden;')
s=s.replace('</style>','#stage{'+'position:relative;width:480px;height:853px;overflow:hidden;padding:18px}\n#endc{position:absolute;inset:0;background:#141416;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;text-align:center}\n#endc .t{font-family:PF;font-weight:900;font-size:44px;letter-spacing:-1px}\n#endc .s{font-family:MONO;font-weight:700;font-size:13px;letter-spacing:2px;color:#ff5a70;margin-top:14px}\n#endc .c{font-size:17px;font-weight:700;margin-top:26px;color:#e8e8ec}\n'+'</style>',1)
s=s.replace('<body><div class="page">','<body><div id="stage"><div class="page">',1)
END=f"""</div>
<div id="endc"><svg width="64" height="64" viewBox="0 0 100 100"><rect x="4" y="4" width="92" height="92" rx="20" fill="#fff" stroke="#fff" stroke-width="4"/><rect x="16" y="22" width="56" height="13" rx="1.5" fill="#111"/><rect x="16" y="41" width="68" height="18" rx="1.5" fill="#e5384f"/><text x="22" y="55" font-family="MONO" font-weight="700" font-size="14" fill="#fff" letter-spacing="2">OTR</text><rect x="16" y="65" width="46" height="13" rx="1.5" fill="#111"/></svg><div class="t">Off the Record</div><div class="s">ISSUE NO. {n} · OUT NOW</div><div class="c">Read it at<br>camrenmulcair.github.io/off-the-record</div></div>
</div>
<script>"""+JSCODE+"""</script></body></html>"""
import re
m=re.search(r'<div class="disc">\s*<span class="lb">[^<]*</span>\s*<p>(.*?)</p>\s*</div>',s,re.S)
nm=re.search(r'<ul class="tnotes"[^>]*>(.*?)</ul>',s,re.S)
DUR=14.5+(4.4 if m else 0)+(4.6 if nm else 0)
if nm:
    lis=re.findall(r'<li(?: data-tag="([^"]*)")?>(.*?)</li>',nm.group(1),re.S)
    s=s.replace('</style>','#ncard{position:absolute;inset:0;background:#141416;color:#fff;display:flex;flex-direction:column;justify-content:center;padding:40px 30px;opacity:0}\n#ncard .lb{align-self:flex-start;font-family:MONO;font-weight:700;font-size:20px;letter-spacing:4px;color:#ff5a70;border:3px solid #ff5a70;padding:5px 12px;border-radius:4px}\n#ncard h4{font-family:PF;font-style:italic;font-weight:700;font-size:30px;margin:18px 0 6px;line-height:1.1}\n#ncard ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}\n#ncard li{display:flex;gap:12px;align-items:flex-start;font-size:18px;font-weight:600;line-height:1.3;opacity:0}\n#ncard li b{flex:none;font-family:MONO;font-size:11.5px;letter-spacing:1.5px;background:#e5384f;color:#fff;padding:4px 7px;border-radius:4px;margin-top:2px}\n#ncard li b.th{background:#0f8b8d}#ncard li b.rc{background:#d4af37;color:#141416}\n</style>',1)
    items=''.join(f'<li><b class="{ {"THANKS":"th","RECORD":"rc"}.get(tag or "NEW","") }">{tag or "NEW"}</b><span>{txt}</span></li>' for tag,txt in lis)
    END=END.replace('<div id="endc">',f'<div id="ncard"><div class="lb">THIS ISSUE</div><h4>Issue No. {n}: what\'s new</h4><ul>{items}</ul></div>\n<div id="endc">',1)
if m:
    s=s.replace('</style>','.page .disc{display:none}\n#dcard{position:absolute;inset:0;background:#f2f3f5;display:flex;flex-direction:column;justify-content:center;padding:44px 34px;opacity:0}\n#dcard .lb{align-self:flex-start;font-family:MONO;font-weight:700;font-size:20px;letter-spacing:4px;color:#c8243b;border:3px solid #c8243b;padding:5px 12px;border-radius:4px;background:rgba(255,255,255,.6)}\n#dcard p{font-size:17px;line-height:1.45;color:#33353c;margin:22px 0 0}\n#dcard strong{color:#111216}\n</style>',1)
    END=END.replace('<div id="endc">','<div id="dcard"><div class="lb">DISCLAIMER</div><p>'+m.group(1)+'</p></div>\n<div id="endc">',1)
i=s.rfind('</div></body></html>')
s=s[:i]+END
tmp=tempfile.mkdtemp(); html=os.path.join(ROOT,'src',f'.trailer{n}.html')
open(html,'w').write(s)
js=os.path.join(tmp,'t.js'); frames=os.path.join(tmp,'f'); os.makedirs(frames)
open(js,'w').write(f"""const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();
const p=await b.newPage({{viewport:{{width:480,height:853}},deviceScaleFactor:2.25}});
await p.goto('file://{html}');await p.waitForTimeout(600);
for(let i=0;i<{int(DUR*30)};i++){{await p.evaluate(t=>setT(t),i/30);
await p.screenshot({{path:`{frames}/f${{String(i).padStart(4,'0')}}.jpg`,type:'jpeg',quality:92}});}}
await b.close();}})();""")
subprocess.run(['node',js],check=True,cwd='/tmp')
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',f'{frames}/f%04d.jpg','-vf','scale=1080:1920:flags=lanczos,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','20','-movflags','+faststart',out],check=True)
os.remove(html); shutil.rmtree(tmp); print('ok',out)
