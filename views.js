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
  }

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
