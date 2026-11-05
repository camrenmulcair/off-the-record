// Render one issue to a single-page PDF (into issues/) and a 5x PNG.
// Usage: node tools/render.js N [pngOutPath]
const path=require('path');const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');const n=process.argv[2];
const png=process.argv[3]||`/home/claude/off-the-record-issue-${n}-hd.png`;
(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:480,height:800},deviceScaleFactor:5});
await p.goto('file://'+path.join(ROOT,'src',`issue${n}.html`));await p.waitForTimeout(500);
await p.screenshot({path:png,fullPage:true});
const h=await p.evaluate(()=>document.documentElement.scrollHeight);
await p.pdf({path:path.join(ROOT,'issues',`off-the-record-issue-${n}.pdf`),width:'480px',height:(h+2)+'px',printBackground:true,pageRanges:'1'});
await b.close();console.log('ok',png);})();
