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
