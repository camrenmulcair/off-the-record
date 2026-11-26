"""Record the live site's three reading views as a 1080x1920, 30 fps, no-sound clip
(about 17.8 s) that plays before the issue trailer (tools/trailer.py --promo).\nCaptions sit in their own band under the page, never on top of it.
Usage: python3 tools/site_promo.py OUT.mp4
Needs playwright (node) and ffmpeg."""
import os, sys, socket, subprocess, shutil, tempfile, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = r'''#tap{position:fixed;z-index:99999;width:54px;height:54px;margin:-27px 0 0 -27px;border-radius:50%;border:4px solid #e5384f;opacity:0;pointer-events:none}
#tc{position:fixed;inset:0;z-index:99999;background:#141416;color:#fff;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:14px;text-align:center;padding:30px}
#tc .st{font-family:MONO,monospace;font-weight:700;font-size:15px;letter-spacing:4px;color:#ff5a70;border:3px solid #ff5a70;padding:5px 12px;border-radius:4px;transform:rotate(-4deg)}
#tc h2{font-family:PF,Georgia,serif;font-style:italic;font-weight:700;font-size:34px;line-height:1.1;margin:6px 0 4px}
#tc .ch{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
#tc .ch span{font-weight:700;font-size:14px;padding:8px 12px;border-radius:999px;background:#23242b;border:1px solid #3a3b42;opacity:0}'''

HTML = ('<div id="tap"></div>'
        '<div id="tc"><div class="st">NEW ON THE SITE</div><h2>Three ways to read<br>Off the Record</h2>'
        '<div class="ch"><span>Latest</span><span>Back issues</span><span>Doomscroll</span></div></div>')

# Runs in the browser. Every scene is a function of t (seconds into the scene) so
# the Node loop only has to step t at 30 fps and take a screenshot.
PAGE_JS = r'''window.F={
$:s=>document.querySelector(s),
seg:(t,a,b)=>Math.max(0,Math.min(1,(t-a)/(b-a))),
eo:x=>1-Math.pow(1-x,3),
E:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,
nat:el=>{const o=el.style.position;el.style.position='static';const y=el.getBoundingClientRect().top+scrollY;el.style.position=o;return y},
go:y=>window.scrollTo(0,Math.max(0,y)),
vt:()=>F.nat(F.$('.views')),
cap:(lbl,txt)=>{window.CAP=[lbl,txt]},
ring:(sel,q)=>{const r=F.$(sel).getBoundingClientRect(),tap=F.$('#tap');tap.style.left=(r.left+r.width/2)+'px';tap.style.top=(r.top+r.height/2)+'px';tap.style.transform='scale('+(0.4+q)+')';tap.style.opacity=1-q},
hideRing:()=>{F.$('#tap').style.opacity=0},
title:t=>{window.CAP=['',''];const tc=F.$('#tc'),st=tc.querySelector('.st'),p=F.seg(t,0,.3);
  st.style.opacity=1;st.style.transform='rotate(-4deg) scale('+(p<1?2.2-1.2*F.eo(p):1)+')';
  tc.querySelectorAll('.ch span').forEach((c,i)=>{c.style.opacity=F.seg(t,.6+.3*i,.8+.3*i)});
  tc.style.opacity=1-F.seg(t,2.1,2.4)},
latest:t=>{F.cap('1 · LATEST',"This week's file, top to bottom.",F.seg(t,0,.2));
  F.go(t<1.2?F.Y0+250*F.E(F.seg(t,0,1.2)):F.Y0+250*(1-F.E(F.seg(t,1.2,1.6))));
  if(t>=1.6)F.ring('.views [data-view="stand"]',F.seg(t,1.6,2.0));else F.hideRing()},
back:t=>{F.scrub(t);const late=t>=2.2;
  F.cap(late?'FOLDERS MATCH THE ISSUE':'2 · BACK ISSUES',late?'War files. Cyber files. Classified.':'Every issue on the newsstand. Tap a folder to open it.',late?1:F.seg(t,0,.2));
  F.go(F.Y0+(F.YE-F.Y0)*F.E(F.seg(t,0,4.0)))},
doomRing:t=>F.ring('.views [data-view="doom"]',F.seg(t,0,.4)),
doom:t=>{const late=t>=2.0;
  F.cap(late?'A FOLDER CLOSES':'3 · DOOMSCROLL',late?'between every issue, then the next one opens.':'Every story ever, back to back. Oldest or newest first.',late?1:F.seg(t,0,.2));
  F.go(t<2.6?F.Y0+(F.A-F.Y0)*F.E(F.seg(t,0,2.6)):F.A+1.2*innerHeight*F.E(F.seg(t,2.6,4.4)))},
calledA:t=>{F.cap('4 · CALLED IT','Every prediction that came true.',F.seg(t,0,.2));
  if(t>=.2&&t<.6)F.ring('.fab',F.seg(t,.2,.6));else F.hideRing()},
calledB:t=>{t+=.6;F.cap('4 · CALLED IT','Tap one to jump straight to it.',1)},
calledC:t=>{t+=2.2;F.cap('4 · CALLED IT','Tap one to jump straight to it.',1);F.ring('a[href="#call-6-1"]',F.seg(t,2.2,2.6))},
prepCalled:()=>{F.hideRing();F.prepLatest()},
prepLatest:()=>{F.$('.views [data-view="latest"]').click();window.ScrollTrigger&&ScrollTrigger.refresh();F.Y0=F.vt();F.go(F.Y0)},
inStand:a=>{const e=a.effect,st=F.$('#stand');return !!(e&&e.target&&st&&st.contains(e.target))},
grab:()=>{F.DA=document.getAnimations().filter(F.inStand);F.DA.forEach(a=>{a.pause();a._t0=0})},
scrub:t=>{document.getAnimations().filter(F.inStand).forEach(a=>{if(F.DA.indexOf(a)<0){a.pause();a._t0=t;F.DA.push(a)}try{a.currentTime=Math.max(0,(t-a._t0)*1000)}catch(e){}})},
release:()=>{(F.DA||[]).forEach(a=>{try{a.finish()}catch(e){try{a.play()}catch(_){}}})},
prepStand:()=>{window.ScrollTrigger&&ScrollTrigger.refresh();F.Y0=F.vt();F.go(F.Y0);const st=F.$('.street');F.YE=F.nat(st)+st.getBoundingClientRect().height-innerHeight},
prepDoom:()=>{window.ScrollTrigger&&ScrollTrigger.refresh();document.querySelectorAll('.reveal').forEach(r=>r.classList.add('in'));
  const cs=[...document.querySelectorAll('main .issue .closer')].filter(c=>getComputedStyle(c.closest('.issue')).display!=='none');
  cs.sort((a,b)=>F.nat(a)-F.nat(b));F.A=F.nat(cs[0])-120;F.Y0=F.vt();F.go(F.Y0)}
};
window.otrLenis&&otrLenis.stop();
document.documentElement.style.scrollBehavior='auto';
'''

NODE_JS = r'''const {chromium}=require('playwright');
const BASE=process.argv[2],FR=process.argv[3],CSS=process.env.SP_CSS,HTML=process.env.SP_HTML,PAGE=process.env.SP_PAGE;
(async()=>{
  const b=await chromium.launch();
  try{
    const ctx=await b.newContext({viewport:{width:360,height:540},deviceScaleFactor:3,isMobile:true,hasTouch:true,colorScheme:'light',reducedMotion:'no-preference'});
    const p=await ctx.newPage();
    await p.goto(BASE+'/index.html');
    await p.waitForTimeout(1000);
    await p.evaluate(([css,html])=>{const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);
      const d=document.createElement('div');d.innerHTML=html;while(d.firstChild)document.body.appendChild(d.firstChild)},[CSS,HTML]);
    await p.evaluate(PAGE);
    let n=0;const caps=[];
    const run=async(name,frames)=>{for(let i=0;i<frames;i++){
      caps[n]=await p.evaluate(([f,t])=>{F[f](t);return window.CAP||['','']},[name,i/30]);
      await p.screenshot({path:`${FR}/f${String(n++).padStart(4,'0')}.jpg`,type:'jpeg',quality:90});}};
    const wait=ms=>p.waitForTimeout(ms);

    // 1. title card, 2.4 s
    await run('title',72);
    await p.evaluate(()=>F.$('#tc').remove());
    // 2. Latest, 2.0 s
    await p.evaluate(()=>F.prepLatest());
    await run('latest',60);
    // 3. Back issues, 4.6 s, then the Doomscroll tap ring, 0.4 s
    await p.evaluate(()=>{F.hideRing();F.$('.views [data-view="stand"]').click()});
    await wait(80);
    await p.evaluate(()=>{F.grab();F.prepStand()});
    await run('back',138);
    await p.evaluate(()=>{F.release();F.go(F.Y0)});
    await run('doomRing',12);
    await p.evaluate(()=>{F.hideRing();F.$('.views [data-view="doom"]').click();F.$('[data-order="old"]').click()});
    await wait(500);
    // 4. Doomscroll, 4.4 s
    await p.evaluate(()=>F.prepDoom());
    await run('doom',132);
    // 5. Called it, 4.0 s: 0-0.6 s caption + ring on the fab, then open it at 0.6 s
    await p.evaluate(()=>F.prepCalled());
    await run('calledA',18);
    await p.evaluate(()=>{F.hideRing();F.$('.fab').click()});
    await run('calledB',48);
    // 2.2 s: ring on the row link for 0.4 s, click it, then shoot in real time (the site scrolls and flashes)
    await run('calledC',12);
    await p.evaluate(()=>{F.hideRing();F.$('a[href="#call-6-1"]').click()});
    for(let i=0;i<42;i++){await wait(33);caps[n]=caps[n-1];
      await p.screenshot({path:`${FR}/f${String(n++).padStart(4,'0')}.jpg`,type:'jpeg',quality:90});}
    // caption band: one picture per distinct caption, 360x100 css px at 3x = 1080x300
    const bp=await (await b.newContext({viewport:{width:360,height:100},deviceScaleFactor:3})).newPage();
    const keys=[...new Set(caps.map(c=>JSON.stringify(c)))];
    for(let k=0;k<keys.length;k++){const [lbl,txt]=JSON.parse(keys[k]);
      await bp.setContent(`<style>@font-face{font-family:MONO;font-weight:700;src:url(${BASE}/fonts/ibm-plex-mono-latin-700-normal.woff2)}
        html,body{margin:0;height:100%;background:#141416}
        body{box-sizing:border-box;border-top:3px solid #e5384f;padding:14px 18px;color:#fff;font:600 17px/1.28 -apple-system,Helvetica,Arial,sans-serif}
        b{display:block;font-family:MONO,monospace;font-size:11.5px;letter-spacing:2px;color:#ff5a70;margin-bottom:5px}</style>
        ${lbl?`<b>${lbl}</b><span>${txt}</span>`:''}`);
      await bp.evaluate(()=>document.fonts.ready);
      await bp.screenshot({path:`${FR}/cap${k}.png`});}
    require('fs').writeFileSync(`${FR}/caps.json`,JSON.stringify(caps.map(c=>keys.indexOf(JSON.stringify(c)))));
    console.log('frames',n);
  }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
'''


def compose(frames):
    import json
    from PIL import Image
    caps = json.load(open(os.path.join(frames, 'caps.json')))
    bands = {}
    for i, k in enumerate(caps):
        if k not in bands:
            bands[k] = Image.open(os.path.join(frames, f'cap{k}.png')).convert('RGB').resize((1080, 300))
        pg = Image.open(os.path.join(frames, f'f{i:04d}.jpg')).convert('RGB').resize((1080, 1620))
        out = Image.new('RGB', (1080, 1920), (20, 20, 22))
        out.paste(pg, (0, 0))
        out.paste(bands[k], (0, 1620))
        out.save(os.path.join(frames, f'c{i:04d}.jpg'), quality=92)


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = os.path.abspath(sys.argv[1])
    port = free_port()
    base = f'http://127.0.0.1:{port}'
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp()
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + '/index.html', timeout=1).read(1)
                break
            except Exception:
                time.sleep(0.2)
        frames = os.path.join(tmp, 'f')
        os.makedirs(frames)
        js = os.path.join(tmp, 'promo.js')
        with open(js, 'w') as f:
            f.write(NODE_JS)
        # the Node script takes its CSS/HTML/page JS from env vars to keep quoting simple
        env = dict(os.environ, SP_CSS=CSS, SP_HTML=HTML, SP_PAGE=PAGE_JS)
        subprocess.run(['node', js, base, frames], check=True, cwd=tmp, env=env)
        compose(frames)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{frames}/c%04d.jpg',
                        '-vf', 'scale=1080:1920:flags=lanczos,format=yuv420p', '-c:v', 'libx264',
                        '-preset', 'veryfast', '-crf', '20', '-movflags', '+faststart', out], check=True)
        print('ok', out)
    finally:
        srv.kill()
        srv.wait()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
