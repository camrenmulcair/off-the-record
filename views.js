/* Three reading views for the preview page. Plain ES5, no libraries.
   Loaded after app.js; only active on views.html. */
(function () {
  'use strict';

  var body = document.body;
  var KEY_VIEW = 'otr-view';
  var KEY_ORDER = 'otr-order';

  var store = {
    get: function (k) {
      try { return window.localStorage.getItem(k); } catch (e) { return null; }
    },
    set: function (k, v) {
      try { window.localStorage.setItem(k, v); } catch (e) { /* private mode: ignore */ }
    }
  };

  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function $(sel) { return document.querySelector(sel); }

  function refresh() {
    window.dispatchEvent(new Event('resize'));
    if (window.ScrollTrigger) window.ScrollTrigger.refresh();
  }

  function scrollToY(y) {
    if (window.otrLenis) window.otrLenis.scrollTo(y, { immediate: true });
    // Lenis can ignore an immediate jump when the page was just moved natively
    // (e.g. a click that scrolled the dossier into view), so set it natively as well.
    window.scrollTo(0, y);
  }

  // height of the pinned view switcher (the only sticky bar now)
  function barH() {
    var el = $('.views');
    return el ? el.getBoundingClientRect().height : 0;
  }

  function scrollToSwitcher() {
    var el = $('.views');
    if (!el) return;
    // the switcher is the pinned top bar, so land it at the very top
    var y = el.getBoundingClientRect().top + window.pageYOffset;
    scrollToY(Math.max(0, y));
  }

  // Document-top offset of an element, from offsetTop up the offsetParent chain.
  // Stories are position:sticky, so getBoundingClientRect is wrong for them once stuck.
  function absTop(el) {
    var y = 0;
    while (el) { y += el.offsetTop; el = el.offsetParent; }
    return y;
  }

  // Hash targets we handle: a "Called it" row (call-N-K) or a story (iN-slug), if it exists.
  function jumpable(hash) {
    var id = (hash || '').replace(/^#/, '');
    if (!(/^call-\d+-\d+$/.test(id) || /^i\d+-/.test(id))) return null;
    return document.getElementById(id) ? id : null;
  }

  function issueOf(id) {
    var m = id.match(/^(?:call-(\d+)-\d+|i(\d+)-)/);
    return parseInt(m[1] || m[2], 10);
  }

  // Jump to a call row or a story: show its issue, close the pop-up, then after the
  // drawer has closed scroll the target under the bar, unredact it, flash it green and
  // keep the hash in sync.
  function jumpTo(id, delay) {
    if (window.otrCloseDrawer) window.otrCloseDrawer();
    if (!body.classList.contains('v-doom')) {
      var n = issueOf(id);
      setView(n === latestN() ? 'latest' : 'one', n);
    }
    setTimeout(function () {
      var el = document.getElementById(id);
      if (!el) return;
      var reveal = el.closest ? el.closest('.reveal') : null;
      [el, reveal].forEach(function (x) {
        if (!x) return;
        x.classList.add('in');
        x.classList.add('revealed');
        $$('.rbar', x).forEach(function (b) { b.remove(); }); // redaction bars: show the text now
      });
      var y = Math.max(0, absTop(el) - barH() - 24);
      if (window.otrLenis) window.otrLenis.scrollTo(y, { duration: 0.9 });
      else window.scrollTo({ top: y, behavior: 'smooth' });
      el.classList.remove('flash');
      void el.offsetWidth; // restart the animation if it is already playing
      el.classList.add('flash');
      setTimeout(function () { el.classList.remove('flash'); }, 2100);
      history.replaceState(null, '', '#' + id);
    }, delay == null ? 350 : delay);
  }

  function revealAll(issues) {
    issues.forEach(function (art) {
      $$('.reveal', art).forEach(function (r) { r.classList.add('in'); });
    });
  }

  // opts.scroll: only the switcher's own buttons scroll to the switcher. Load and
  // issue-link paths pass false so app.js (which scrolls to #issue anchors) is not fought.
  function setView(v, n, opts) {
    var views = ['latest', 'stand', 'doom', 'one'];
    var doScroll = !!(opts && opts.scroll);
    if (views.indexOf(v) === -1) v = 'latest';

    views.forEach(function (x) { body.classList.remove('v-' + x); });
    body.classList.add('v-' + v);

    // segmented control: "one" reads as Back issues (you came from there)
    var pressed = v === 'one' ? 'stand' : v;
    $$('.views button[data-view]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-view') === pressed ? 'true' : 'false');
    });

    var stand = $('#stand');
    if (stand) stand.hidden = v !== 'stand';
    var order = $('.doomorder');
    if (order) order.hidden = v !== 'doom';

    var issues = $$('main > .issue');
    if (v === 'one') {
      issues.forEach(function (art) { art.classList.remove('on'); });
      var target = $('#issue-' + n);
      if (target) target.classList.add('on');
      var shown = target ? [target] : [];
      revealAll(shown);
    } else {
      issues.forEach(function (art) { art.classList.remove('on'); });
      if (v === 'doom') revealAll(issues);
    }

    if (v === 'latest' || v === 'stand' || v === 'doom') store.set(KEY_VIEW, v);

    refresh();
    if (doScroll) scrollToSwitcher();
    // entering the newsstand: the files fall onto the shelves
    if (v === 'stand' && prevView !== 'stand') {
      requestAnimationFrame(function () { requestAnimationFrame(dropIn); });
    }
    prevView = v;
  }

  // ---- Back issues: the kiosk lights up and the files fall into place ----
  // Everything is a Web Animation (no timers), so it can be paused or scrubbed, and
  // every animation ends on the element's resting CSS so nothing jumps when it finishes.
  var prevView = null, drops = [];
  var REDUCE = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function anim(el, kf, o) {
    if (!el || !el.animate) return null;
    try { var a = el.animate(kf, o); drops.push(a); return a; } catch (e) { return null; }
  }
  function dust(d, at) {
    var w = d.offsetWidth;
    for (var k = 0; k < 8; k++) {
      var left = k < 4, s = 4 + Math.random() * 7;
      var p = document.createElement('i');
      p.className = 'dust'; p.setAttribute('aria-hidden', 'true');
      p.style.width = p.style.height = s + 'px';
      p.style.left = (left ? 4 + Math.random() * 22 : w - 26 + Math.random() * 22) + 'px';
      d.appendChild(p);
      var dx = (left ? -1 : 1) * (16 + Math.random() * 38), dy = -(8 + Math.random() * 18);
      var a = anim(p, [
        { transform: 'translate(0,0) scale(.4)', opacity: 0.9 },
        { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(1.7)', opacity: 0 }
      ], { duration: 520 + Math.random() * 220, delay: at, easing: 'cubic-bezier(.1,.8,.3,1)', fill: 'both' });
      if (a) a.onfinish = (function (el) { return function () { el.remove(); }; })(p);
      else p.remove();
    }
  }
  var dropIO = null;
  function dropOne(d, idx, delay, fall, fade, shelf) {
    var tilt = idx % 2 ? 1 : -1.2;  // matches .rack .dossier / :nth-child(even)
    var spin = (idx % 3 === 0 ? -1 : 1) * (5 + Math.random() * 7);
    var dur = 950, impact = 0.55, land = delay + dur * impact;
    anim(d, [
      { transform: 'translateY(' + -fall + 'px) rotate(' + (tilt + spin) + 'deg)', opacity: fade ? 0 : 1, easing: 'cubic-bezier(.55,0,1,.55)' },
      { opacity: 1, offset: fade ? 0.18 : 0.01 },
      { transform: 'translateY(0) rotate(' + tilt + 'deg) scale(1.04,.93)', offset: impact, easing: 'cubic-bezier(.2,.7,.4,1)' },
      { transform: 'translateY(-16px) rotate(' + (tilt - spin * 0.25) + 'deg) scale(.99,1.02)', offset: 0.72, easing: 'cubic-bezier(.6,0,.9,.5)' },
      { transform: 'translateY(0) rotate(' + tilt + 'deg) scale(1.02,.97)', offset: 0.86, easing: 'ease-out' },
      { transform: 'translateY(-3px) rotate(' + tilt + 'deg)', offset: 0.93 },
      { transform: 'translateY(0) rotate(' + tilt + 'deg)', opacity: 1 }
    ], { duration: dur, delay: delay, fill: 'backwards' });
    // thud: dust puffs out from under the folder
    dust(d, land);
    // the clip snaps down, then the stamp slams on
    anim(d, [{ transform: 'translateY(-28px)', opacity: 0 }, { transform: 'translateY(2px)', opacity: 1, offset: 0.7 },
      { transform: 'translateY(0)', opacity: 1 }], { duration: 220, delay: land + 70, easing: 'ease-in', fill: 'backwards', pseudoElement: '::before' });
    anim($('.d-st', d), [{ transform: 'rotate(-9deg) scale(2.6)', opacity: 0 },
      { transform: 'rotate(-9deg) scale(.92)', opacity: 1, offset: 0.7 }, { transform: 'rotate(-9deg) scale(1)', opacity: 1 }],
      { duration: 280, delay: land + 200, easing: 'cubic-bezier(.2,.8,.3,1)', fill: 'backwards' });
    if (d.classList.contains('th-war')) {
      anim($('.d-holes', d), [{ opacity: 0 }, { opacity: 1 }], { duration: 60, delay: land + 420, easing: 'steps(1,end)', fill: 'backwards' });
    }
  }
  function dropIn() {
    var stand = $('#stand');
    if (REDUCE || !stand || stand.hidden || !stand.animate) return;
    drops.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    drops = [];
    $$('.dust', stand).forEach(function (x) { x.remove(); });
    var vh = window.innerHeight;

    // the kiosk wakes up: sign flickers on, bulbs light left to right, placard drops, card swings in
    anim($('.roof .sign', stand), [{ opacity: 0 }, { opacity: 1, offset: 0.15 }, { opacity: 0.15, offset: 0.25 },
      { opacity: 1, offset: 0.4 }, { opacity: 0.4, offset: 0.5 }, { opacity: 1 }], { duration: 900, fill: 'backwards' });
    anim($('.roof .bulbs', stand), [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }],
      { duration: 700, delay: 120, easing: 'steps(12,end)', fill: 'backwards' });
    anim($('h2', stand), [
      { transform: 'translateY(-90px) rotate(-14deg)', opacity: 0, easing: 'cubic-bezier(.5,0,.9,.5)' },
      { transform: 'translateY(0) rotate(-2deg)', opacity: 1, offset: 0.6, easing: 'ease-out' },
      { transform: 'translateY(-7px) rotate(-3deg)', offset: 0.8, easing: 'ease-in' },
      { transform: 'translateY(0) rotate(-2deg)' }], { duration: 700, delay: 80, fill: 'backwards' });
    anim($('.sub', stand), [{ transform: 'scale(.6) rotate(8deg)', opacity: 0 },
      { transform: 'scale(1.06) rotate(0deg)', opacity: 1, offset: 0.7 }, { transform: 'scale(1) rotate(1.2deg)', opacity: 1 }],
      { duration: 420, delay: 420, easing: 'ease-out', fill: 'backwards' });
    anim($('.card.c1', stand), [{ transform: 'rotate(75deg) scale(.8)', opacity: 0 },
      { transform: 'rotate(-10deg) scale(1)', opacity: 1, offset: 0.5 }, { transform: 'rotate(14deg)', offset: 0.72 },
      { transform: 'rotate(3deg)', offset: 0.88 }, { transform: 'rotate(6deg)' }],
      { duration: 1100, delay: 320, easing: 'ease-out', fill: 'backwards' });

    // the files: drop from above, squash on the shelf, bounce, settle at their tilt.
    // Files on screen fall from above the top edge; the rest wait out of sight and
    // drop in when you scroll down to them.
    var shelf = $('.stand-in', stand);
    var ds = $$('.rack .dossier', stand), t0 = 520, gap = 115;
    if (dropIO) { dropIO.disconnect(); dropIO = null; }
    ds.forEach(function (d) { d.classList.remove('waiting'); });
    var onscreen = ds.filter(function (d) { return d.getBoundingClientRect().top < vh - 40; });
    onscreen.forEach(function (d, i) {
      dropOne(d, ds.indexOf(d), t0 + i * gap, d.getBoundingClientRect().bottom + 60, false, shelf);
    });
    var later = ds.filter(function (d) { return onscreen.indexOf(d) === -1; });
    if (later.length && 'IntersectionObserver' in window) {
      var k = 0;
      later.forEach(function (d) { d.classList.add('waiting'); });
      dropIO = new IntersectionObserver(function (en) {
        en.forEach(function (x) {
          if (!x.isIntersecting) return;
          dropIO.unobserve(x.target);
          x.target.classList.remove('waiting');
          dropOne(x.target, ds.indexOf(x.target), (k++ % 2) * gap, 340, true, shelf);
        });
      }, { rootMargin: '0px 0px -12% 0px' });
      later.forEach(function (d) { dropIO.observe(d); });
    } else {
      later.forEach(function (d, i) { dropOne(d, ds.indexOf(d), t0 + (onscreen.length + i) * gap, 340, true, shelf); });
    }

    // below the booth: papers stack up on the counter, the crate and box slide in from the curb
    var after = t0 + onscreen.length * gap + 250;
    $$('.counter .stack', stand).forEach(function (s, i) {
      var rest = i === 1 ? 'rotate(1deg)' : 'rotate(-1deg)';
      anim(s, [{ transform: 'translateY(70px) ' + rest }, { transform: 'translateY(-6px) ' + rest, offset: 0.7 }, { transform: 'translateY(0) ' + rest }],
        { duration: 500, delay: after + i * 90, easing: 'ease-out', fill: 'backwards' });
    });
    [['.street .crate', 'none'], ['.street .box', 'none'], ['.street .card.c2', 'rotate(-5deg)']].forEach(function (p, i) {
      anim($(p[0], stand), [{ transform: 'translateX(-260px) ' + (p[1] === 'none' ? '' : p[1]) },
        { transform: 'translateX(8px) ' + (p[1] === 'none' ? '' : p[1]), offset: 0.8 }, { transform: p[1] }],
        { duration: 600, delay: after + 200 + i * 110, easing: 'cubic-bezier(.2,.8,.3,1)', fill: 'backwards' });
    });
  }
  window.otrDropIn = dropIn;

  function setOrder(o) {
    if (o !== 'old') o = 'new';
    $$('main > .issue').forEach(function (art) {
      var n = parseInt(art.getAttribute('data-n'), 10) || 0;
      art.style.order = o === 'old' ? String(n) : String(-n);
    });
    $$('.doomorder button[data-order]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-order') === o ? 'true' : 'false');
    });
    store.set(KEY_ORDER, o);
    refresh();
  }

  // Click delegation. app.js listens on document, so this runs first for our attributes.
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) return;

    var vb = t.closest('[data-view]');
    if (vb) { setView(vb.getAttribute('data-view'), null, { scroll: true }); return; }

    var ob = t.closest('[data-open]');
    if (ob) { setView('one', ob.getAttribute('data-open'), { scroll: true }); return; }

    var od = t.closest('[data-order]');
    if (od) { setOrder(od.getAttribute('data-order')); return; }
  });

  // Issue links in the jump nav and the covers: capture on window so this fires before app.js.
  window.addEventListener('click', function (e) {
    var bk = e.target && e.target.closest ? e.target.closest('a[href="#back"]') : null;
    if (bk) { e.preventDefault(); e.stopPropagation(); setView('stand', null, { scroll: true }); return; }
    // "Called it" rows and story links (#call-N-K, #iN-slug): jump to the target
    var jl = e.target && e.target.closest ? e.target.closest('a[href^="#call-"], a[href^="#i"]') : null;
    var jid = jl ? jumpable(jl.getAttribute('href')) : null;
    if (jid) {
      e.preventDefault(); e.stopPropagation();
      jumpTo(jid);
      return;
    }
    var a = e.target && e.target.closest ? e.target.closest('a[href^="#issue-"]') : null;
    if (!a) return;
    if (body.classList.contains('v-doom')) return;
    var n = parseInt(a.getAttribute('href').replace('#issue-', ''), 10);
    if (!n) return;
    if (n === latestN()) setView('latest'); else setView('one', n);
  }, true);

  function latestN() {
    var first = $('main > .issue.latest') || $('main > .issue');
    return first ? parseInt(first.getAttribute('data-n'), 10) : null;
  }

  function init() {
    var hash = window.location.hash || '';
    var m = hash.match(/^#issue-(\d+)$/);
    var s = hash.match(/^#i(\d+)-/);
    var jid = jumpable(hash);
    var saved = store.get(KEY_VIEW);
    var order = store.get(KEY_ORDER) || 'new';

    setOrder(order);

    if (m) {
      var n = parseInt(m[1], 10);
      if (n === latestN()) setView('latest');
      else setView('one', n);
    } else if (jid) {
      // a shared "Called it" or story link: show its issue, then jump to it once the page has settled
      if (saved === 'doom') setView('doom');
      jumpTo(jid, 600);
    } else if (s) {
      setView('one', parseInt(s[1], 10));
    } else {
      setView(saved || 'latest');
    }
    // (no scroll on load: the cover comes first)
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
