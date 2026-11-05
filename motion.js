// Reveals stories as they scroll into view. Content is fully visible without JS
// or when the reader has "reduce motion" turned on.
(function(){
  var els=document.querySelectorAll('.reveal');
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce||!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')});return;}
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target);}});
  },{rootMargin:'0px 0px -12% 0px',threshold:0.15});
  els.forEach(function(e){io.observe(e)});
})();
