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
  })});

  // Compact archive (off by default, remembered per reader)
  var cb=$('#compact');
  function setCompact(on){d.body.classList.toggle('compact-on',on);cb.checked=on;store.set('otr-compact',on?'1':'0')}
  setCompact(store.get('otr-compact')==='1');
  cb.addEventListener('change',function(){setCompact(cb.checked)});
  $$('.expand').forEach(function(b){b.addEventListener('click',function(){var a=b.closest('.issue');a.classList.add('open');$$('.reveal',a).forEach(function(e){e.classList.add('in')})})});

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
  d.addEventListener('click',function(e){if(e.target.closest('.fl,.expand,#compact,.toggle,summary'))setTimeout(function(){placeCards();frame()},60)});
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
  // Cover: masthead starts redacted; stamp slams, bars sweep off, then the file tilts away
  var tl=gsap.timeline({scrollTrigger:{trigger:'#cover .pin',start:'top top',end:'+=130%',pin:true,scrub:0.6}});
  tl.to('#hint',{opacity:0,duration:.1},0)
    .fromTo('#cstamp',{opacity:1,scale:2.6,rotate:-9},{scale:1,rotate:-9,duration:.22,ease:'back.out(3)'},.04)
    .to('#cover .bars i',{xPercent:110,duration:.28,stagger:.04,ease:'power2.in'},.3)
    .to('#folder',{yPercent:-55,scale:.72,rotate:-5,opacity:.12,duration:.4,ease:'power2.in'},.62);
  // Every issue: vertical scroll slides the covers sideways
  var strip=document.getElementById('strip');
  if(strip){
    gsap.to(strip,{x:function(){return -Math.max(0,strip.scrollWidth-strip.parentNode.clientWidth)},ease:'none',
      scrollTrigger:{trigger:'#back .pin',start:'top top',end:function(){return '+='+Math.max(1,strip.scrollWidth-strip.parentNode.clientWidth)},pin:true,scrub:0.5,invalidateOnRefresh:true}});
  }
  // keep pinned sections in sync when compact mode/filters change the page height
  document.addEventListener('click',function(e){if(e.target.closest('.fl,.expand,#compact,.toggle,summary'))setTimeout(function(){ScrollTrigger.refresh()},80)});
  addEventListener('load',function(){ScrollTrigger.refresh()});
})();
