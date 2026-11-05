// Off the Record site behaviour. Everything degrades gracefully: without JS the
// whole archive is visible; with "reduce motion" on, nothing animates.
(function(){
  var d=document, $=function(q,el){return (el||d).querySelector(q)}, $$=function(q,el){return [].slice.call((el||d).querySelectorAll(q))};
  var store={get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
  var toastT, toast=function(msg){var t=$('#toast');t.textContent=msg;t.classList.add('on');clearTimeout(toastT);toastT=setTimeout(function(){t.classList.remove('on')},1800)};

  // Scroll reveal
  var els=$$('.reveal'), reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce||!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')})}
  else{var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{rootMargin:'0px 0px -12% 0px',threshold:0.15});els.forEach(function(e){io.observe(e)})}
  // Anything opened via a link (#story) should be revealed immediately
  function revealHash(){var t=location.hash&&d.getElementById(location.hash.slice(1));if(t){t.classList.add('in');var a=t.closest('.issue');if(a)a.classList.add('open')}}
  revealHash(); window.addEventListener('hashchange',revealHash);

  // Section filters
  $$('.fl').forEach(function(b){b.addEventListener('click',function(){
    var f=b.dataset.f;
    $$('.fl').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
    $$('.ibody > *').forEach(function(el){
      var ef=el.dataset.f;
      el.classList.toggle('is-hidden', f!=='all' && ef!==f);
      if(f!=='all') el.classList.add('in');
    });
    $$('.issue').forEach(function(a){var any=$$('.ibody > [data-f]:not(.is-hidden)',a).length;a.classList.toggle('is-hidden',f!=='all'&&!any)});
    $('#announce').textContent=f==='all'?'Showing every section':'Showing '+b.textContent+' only';
    if(window.ScrollTrigger)ScrollTrigger.refresh();
    var first=f==='all'?null:$('.ibody > [data-f="'+f+'"]:not(.is-hidden)');
    if(first){var y=first.getBoundingClientRect().top+scrollY-120;
      if(window.otrLenis)window.otrLenis.scrollTo(y,{duration:.8});else scrollTo({top:y,behavior:'smooth'})}
  })});

  // Show all issues (off by default: latest issue + back-issue strip)
  var sa=$('#showall');
  function setAll(on){d.body.classList.toggle('show-all',on);if(sa)sa.checked=on;
    $$('.issue:not(.latest) .reveal').forEach(function(e){e.classList.add('in')});
    if(window.ScrollTrigger)setTimeout(function(){ScrollTrigger.refresh()},50)}
  if(sa)sa.addEventListener('change',function(){setAll(sa.checked)});
  // Links to an older issue (covers, Called it list) open everything first, then scroll there
  d.addEventListener('click',function(e){
    var a=e.target.closest('a[href^="#issue-"]'); if(!a)return;
    var t=d.getElementById(a.getAttribute('href').slice(1)); if(!t)return;
    e.preventDefault(); closeDrawer();
    if(!t.classList.contains('latest')&&!d.body.classList.contains('show-all'))setAll(true);
    setTimeout(function(){var y=t.getBoundingClientRect().top+scrollY-60;
      if(window.otrLenis)window.otrLenis.scrollTo(y,{duration:1});else scrollTo({top:y,behavior:'smooth'});
      history.replaceState(null,'',a.getAttribute('href'))},120);
  },true);

  // Called it drawer (slides in from the side)
  var drawer=$('#calls'), bg=$('#drawer-bg'), cbtn=$('.calls-btn'), lastFocus=null;
  function openDrawer(){if(!drawer)return;lastFocus=d.activeElement;drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');bg.hidden=false;
    requestAnimationFrame(function(){bg.classList.add('on')});if(cbtn)cbtn.setAttribute('aria-expanded','true');
    if(window.otrLenis)window.otrLenis.stop();$('.drawer-x',drawer).focus()}
  function closeDrawer(){if(!drawer||!drawer.classList.contains('open'))return;drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');bg.classList.remove('on');
    setTimeout(function(){bg.hidden=true},250);if(cbtn)cbtn.setAttribute('aria-expanded','false');if(window.otrLenis)window.otrLenis.start();if(lastFocus)lastFocus.focus()}
  if(cbtn)cbtn.addEventListener('click',function(){drawer.classList.contains('open')?closeDrawer():openDrawer()});
  if(bg)bg.addEventListener('click',closeDrawer);
  if(drawer)$('.drawer-x',drawer).addEventListener('click',closeDrawer);
  d.addEventListener('keydown',function(e){if(e.key==='Escape')closeDrawer()});
  window.otrCloseDrawer=closeDrawer;

  // Share one story
  $$('.share').forEach(function(b){b.addEventListener('click',function(){
    var url=location.origin+location.pathname+'#'+b.dataset.id, title=b.dataset.title+' · Off the Record';
    if(navigator.share){navigator.share({title:title,url:url}).catch(function(){})}
    else if(navigator.clipboard){navigator.clipboard.writeText(url).then(function(){toast('Link copied')},function(){prompt('Copy this link',url)})}
  })});

  // Listen (reads the issue aloud with the phone's own voice)
  var speaking=null;
  $$('.listen').forEach(function(b){
    if(!('speechSynthesis' in window)){b.hidden=true;return}
    b.addEventListener('click',function(){
      var a=b.closest('.issue');
      if(speaking===a){speechSynthesis.cancel();return}
      speechSynthesis.cancel();
      var parts=[$('h2',a).textContent+'.'];
      $$('.ibody > *:not(.is-hidden)',a).forEach(function(el){
        $$('h3,h4,.dek,.bl,.story p,.brk p,.row b,.row span',el).forEach(function(t){parts.push(t.textContent.trim())});
      });
      var u=new SpeechSynthesisUtterance(parts.join(' \n'));u.lang='en-CA';u.rate=1;
      u.onend=u.onerror=function(){speaking=null;$$('.listen').forEach(function(x){x.setAttribute('aria-pressed','false');x.innerHTML='<span aria-hidden="true">▶</span> Listen'})};
      speaking=a; b.setAttribute('aria-pressed','true'); b.innerHTML='<span aria-hidden="true">■</span> Stop';
      speechSynthesis.speak(u);
    });
  });
})();

// ---- v3: pinned cover, stacking cards, called-it stamps (scroll-driven) ----
(function(){
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce) return;
  var d=document, cover=d.getElementById('cover'), folder=d.getElementById('folder'), stamp=d.getElementById('cstamp'), hint=d.getElementById('hint');
  var cards=[].slice.call(d.querySelectorAll('.ibody > .story, .ibody > .brk'));
  var rows=[].slice.call(d.querySelectorAll('.score .row'));
  var clamp=function(x){return Math.max(0,Math.min(1,x))}, ease=function(t){return 1-Math.pow(1-t,3)};
  // Stick each card so its whole text has scrolled into view before the next one slides over it
  function placeCards(){
    var vh=innerHeight, groups={};
    cards.forEach(function(c){var k=c.parentNode;groups[k.parentNode.id]=(groups[k.parentNode.id]||0)+1;var i=groups[k.parentNode.id];
      c.style.top=Math.min(64+i*6, vh-c.offsetHeight-12)+'px';});
  }
  function frame(){
    var vh=innerHeight;
    rows.forEach(function(row){var b=row.getBoundingClientRect();var t=clamp((vh*0.8-b.top)/(vh*0.2));
      var e=t<1?2.4-1.4*ease(t):1;var st=row.querySelector('.ci');if(st){st.style.setProperty('--s',e);st.style.setProperty('--o',t>0?1:0)}});
  }
  var tick=false;
  addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(function(){frame();tick=false})}},{passive:true});
  addEventListener('resize',function(){placeCards();frame()});
  // re-measure when compact mode or filters change card heights
  d.addEventListener('click',function(e){if(e.target.closest('.fl,.expand,#showall,.toggle,summary'))setTimeout(function(){placeCards();frame()},60)});
  if(d.fonts&&d.fonts.ready)d.fonts.ready.then(placeCards);
  placeCards(); frame();
})();

// ---- v4: Lenis smooth scrolling + GSAP cover and sideways issue strip ----
(function(){
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce||!window.gsap||!window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);
  if(window.Lenis){
    var lenis=new Lenis({lerp:0.09,smoothWheel:true,anchors:{offset:-56}});
    lenis.on('scroll',ScrollTrigger.update);
    gsap.ticker.add(function(t){lenis.raf(t*1000)}); gsap.ticker.lagSmoothing(0);
    window.otrLenis=lenis;
  }
  // Cover: everything on the masthead starts blacked out; the bars wipe off, THEN the stamp slams, then the file leaves
  var mast=document.getElementById('folder'), bars=[];
  ['.logo','h1','.tg','.il','.il2'].forEach(function(q){var el=mast.querySelector(q);if(!el)return;
    var b=document.createElement('i');b.className='mbar';b.setAttribute('aria-hidden','true');mast.appendChild(b);bars.push([b,el])});
  // Position bars without touching their transform (GSAP owns that), and only when the width really changes
  function placeBars(){var m=mast.getBoundingClientRect(),sc=m.width/mast.offsetWidth||1;
    bars.forEach(function(p){var el=p[1],r;
      if(el.tagName.toLowerCase()==='svg'){r=el.getBoundingClientRect()}else{var rg=document.createRange();rg.selectNodeContents(el);r=rg.getBoundingClientRect()}
      var st=p[0].style;st.left=((r.left-m.left)/sc-6)+'px';st.top=((r.top-m.top)/sc-3)+'px';st.width=(r.width/sc+12)+'px';st.height=(r.height/sc+6)+'px'})}
  var lastW=innerWidth;
  placeBars(); if(document.fonts&&document.fonts.ready)document.fonts.ready.then(placeBars);
  addEventListener('resize',function(){if(innerWidth!==lastW){lastW=innerWidth;placeBars()}});
  ScrollTrigger.config({ignoreMobileResize:true});
  var tl=gsap.timeline({scrollTrigger:{trigger:'#cover .pin',start:'top top',end:'+=150%',pin:true,scrub:0.6}});
  tl.to('#hint',{opacity:0,duration:.08},0)
    .to(bars.map(function(p){return p[0]}),{scaleX:0,transformOrigin:'right center',duration:.3,stagger:.06,ease:'power2.inOut'},.02)
    .fromTo('#cstamp',{opacity:0,scale:2.6,rotate:-9},{opacity:1,scale:1,rotate:-9,duration:.18,ease:'back.out(3)',immediateRender:false},.52)
    .to('#folder',{yPercent:-55,scale:.72,rotate:-5,opacity:.12,duration:.3,ease:'power2.in'},.78);
  // Every issue: vertical scroll slides the covers sideways
  var strip=document.getElementById('strip');
  if(strip){
    gsap.to(strip,{x:function(){return -Math.max(0,strip.scrollWidth-strip.parentNode.clientWidth)},ease:'none',
      scrollTrigger:{trigger:'#back .pin',start:'top top',end:function(){return '+='+Math.max(1,strip.scrollWidth-strip.parentNode.clientWidth)},pin:true,scrub:0.5,invalidateOnRefresh:true}});
  }
  // keep pinned sections in sync when compact mode/filters change the page height
  document.addEventListener('click',function(e){if(e.target.closest('.fl,.expand,#showall,.toggle,summary'))setTimeout(function(){ScrollTrigger.refresh()},80)});
  addEventListener('load',function(){ScrollTrigger.refresh()});
})();

// ---- v7: redaction bars sit on top of every line of text, then wipe off when the story arrives ----
(function(){
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce) return;
  var d=document, cards=[].slice.call(d.querySelectorAll('.ibody > .story, .ibody > .brk'));
  var groups=[['.hl span',0.12,'h'],['.dek .rd',0.38,''],['.bl .rd, .brk > p .rd, .story > p .rd',0.62,'']];
  function build(card){
    [].slice.call(card.querySelectorAll('.rbar')).forEach(function(b){b.remove()});
    if(card.classList.contains('revealed'))return;
    var cr=card.getBoundingClientRect(), ox=cr.left+card.clientLeft, oy=cr.top+card.clientTop;
    groups.forEach(function(g){
      [].slice.call(card.querySelectorAll(g[0])).forEach(function(el){
        [].slice.call(el.getClientRects()).forEach(function(r,i){
          if(r.width<2)return;
          var b=d.createElement('i');b.className='rbar'+(g[2]?' '+g[2]:'');b.setAttribute('aria-hidden','true');
          b.style.left=(r.left-ox-3)+'px';b.style.top=(r.top-oy-1)+'px';b.style.width=(r.width+6)+'px';b.style.height=(r.height+2)+'px';
          b.style.transitionDelay=(g[1]+i*0.07)+'s';card.appendChild(b);
        });
      });
    });
  }
  function reveal(card){if(card.classList.contains('revealed'))return;card.classList.add('revealed');
    [].slice.call(card.querySelectorAll('.rbar')).forEach(function(b){requestAnimationFrame(function(){b.classList.add('gone')})});
    setTimeout(function(){[].slice.call(card.querySelectorAll('.rbar')).forEach(function(b){b.remove()})},2200)}
  function buildAll(){cards.forEach(function(c){if(c.offsetParent!==null)build(c)})}
  // reveal when the reveal-on-scroll class lands
  var mo=new MutationObserver(function(ms){ms.forEach(function(m){var c=m.target;if(c.classList.contains('in')&&!c.classList.contains('revealed'))setTimeout(function(){reveal(c)},120)})});
  cards.forEach(function(c){mo.observe(c,{attributes:true,attributeFilter:['class']})});
  var lastW=innerWidth;
  function init(){buildAll();cards.forEach(function(c){if(c.classList.contains('in'))reveal(c)})}
  if(d.fonts&&d.fonts.ready)d.fonts.ready.then(init);else init();
  addEventListener('resize',function(){if(innerWidth!==lastW){lastW=innerWidth;buildAll()}});
  // cards that were hidden (filters / show all) have nothing to cover when they appear
  d.addEventListener('click',function(e){if(e.target.closest('.fl,#showall,.toggle,a[href^="#issue-"]'))setTimeout(function(){cards.forEach(function(c){if(c.offsetParent!==null&&!c.classList.contains('revealed')&&c.classList.contains('in'))reveal(c)})},200)});
})();
