// TACTIC static site — small, dependency-free behaviours.
// Everything that reacts to scrolling runs in ONE requestAnimationFrame callback,
// so the page does at most one round of work per frame however fast you scroll.
(function () {
  "use strict";

  var root = document.documentElement;
  var reduceMQ = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduce = function () { return reduceMQ.matches; };
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  /* ------------------------------------------------ scroll loop ------ */
  var scrollJobs = [];
  var ticking = false;
  function runScrollJobs() {
    ticking = false;
    for (var i = 0; i < scrollJobs.length; i++) scrollJobs[i]();
  }
  function requestTick() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(runScrollJobs); }
  }
  window.addEventListener("scroll", requestTick, { passive: true });
  window.addEventListener("resize", requestTick, { passive: true });

  /* ------------------------------------------------ header ----------- */
  var header = $(".site-header");
  var toggle = $(".menu-toggle");
  var panel = $("#site-menu");

  if (header) {
    scrollJobs.push(function () {
      header.classList.toggle("scrolled", window.scrollY > 8);
    });
  }

  function setMenu(open, returnFocus) {
    if (!header || !toggle) return;
    header.classList.toggle("open", open);
    root.classList.toggle("menu-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    if (!open && returnFocus) toggle.focus();
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      setMenu(!header.classList.contains("open"));
    });
    // Tapping a link closes the menu (also matters for same-page links)
    if (panel) panel.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    // Rotating a tablet / widening the window past the breakpoint closes it
    window.matchMedia("(min-width: 921px)").addEventListener("change", function (e) {
      if (e.matches) setMenu(false);
    });
  }

  /* Product dropdown (desktop) */
  var groups = $$(".nav-group");
  function closeGroups(except) {
    groups.forEach(function (g) {
      if (g === except) return;
      g.classList.remove("open");
      $(".nav-trigger", g).setAttribute("aria-expanded", "false");
    });
  }
  groups.forEach(function (group) {
    var btn = $(".nav-trigger", group);
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = !group.classList.contains("open");
      closeGroups(group);
      group.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Tabbing out of the menu closes it
    group.addEventListener("focusout", function (e) {
      if (!group.contains(e.relatedTarget)) closeGroups();
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-group")) closeGroups();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var openGroup = $(".nav-group.open");
    if (openGroup) { closeGroups(); $(".nav-trigger", openGroup).focus(); }
    if (header && header.classList.contains("open")) setMenu(false, true);
  });

  /* ------------------------------------------------ hero ------------- */
  // Gentle depth: the two floating cards drift up a little faster than the page.
  var floats = $$(".hero-stage .float img");
  if (floats.length) {
    scrollJobs.push(function () {
      if (reduce() || window.innerWidth < 761) return;
      var y = window.scrollY;
      if (y > window.innerHeight * 1.5) return; // hero is long gone; leave it
      floats.forEach(function (im, k) {
        var shift = -Math.min(y * (k ? 0.05 : 0.09), 60);
        im.style.transform = "translate3d(0," + shift.toFixed(1) + "px,0)";
      });
    });
  }

  /* ------------------------------------------------ logo marquee ----- */
  // Stop animating while it's off screen (saves battery on long pages).
  var marquee = $(".marquee");
  if (marquee && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      marquee.classList.toggle("is-paused", !entries[0].isIntersecting);
    }).observe(marquee);
  }

  /* ------------------------------------------------ feature tabs ----- */
  // All panels sit in the same grid cell (see style.css), so the section never
  // changes height. Switching only cross-fades.
  $$("[data-tabs]").forEach(function (box) {
    var list = $('[role="tablist"]', box);
    var tabs = $$('[role="tab"]', box);
    var panels = $$('[role="tabpanel"]', box);

    function revealPill(t) {
      if (list.scrollWidth <= list.clientWidth) return;
      var l = list.getBoundingClientRect(), r = t.getBoundingClientRect();
      var left = list.scrollLeft + (r.left - l.left) - (l.width - r.width) / 2;
      list.scrollTo({ left: left, behavior: reduce() ? "auto" : "smooth" }); // sideways only
    }
    function select(i, focus) {
      tabs.forEach(function (t, k) {
        t.setAttribute("aria-selected", k === i ? "true" : "false");
        t.tabIndex = k === i ? 0 : -1;
      });
      panels.forEach(function (p, k) {
        p.classList.toggle("is-active", k === i);
        if (k === i) p.removeAttribute("inert"); else p.setAttribute("inert", "");
      });
      if (focus) tabs[i].focus({ preventScroll: true });
      revealPill(tabs[i]);
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(i); });
      t.addEventListener("keydown", function (e) {
        var n = tabs.length, to = null;
        if (e.key === "ArrowRight") to = (i + 1) % n;
        if (e.key === "ArrowLeft") to = (i - 1 + n) % n;
        if (e.key === "Home") to = 0;
        if (e.key === "End") to = n - 1;
        if (to !== null) { e.preventDefault(); select(to, true); }
      });
    });
    // initial state without moving anything
    tabs.forEach(function (t, k) { t.tabIndex = k === 0 ? 0 : -1; });
    panels.forEach(function (p, k) { if (k) p.setAttribute("inert", ""); });
  });

  /* ------------------------------------------------ how it works ----- */
  // A "reading line" sits 45% down the screen. The step whose number has
  // crossed it is lit, the line down the list fills to it, and the pinned
  // window cross-fades to that step's screenshot.
  var how = $(".how");
  if (how) {
    var steps = $(".steps-lit", how);
    var items = $$(":scope > li", steps);
    var shots = $$(".how-visual .stage > img", how);
    var centers = [];
    var current = -1;

    var measure = function () {
      var top = steps.getBoundingClientRect().top;
      centers = items.map(function (li) {
        var t = $(".tile", li).getBoundingClientRect();
        return t.top - top + t.height / 2;
      });
      steps.style.setProperty("--track-top", centers[0] + "px");
      steps.style.setProperty("--track-h", (centers[centers.length - 1] - centers[0]) + "px");
      update();
    };
    var update = function () {
      if (!centers.length) return;
      var r = steps.getBoundingClientRect();
      if (r.bottom < -200 || r.top > window.innerHeight + 200) return; // off screen
      var line = window.innerHeight * 0.45 - r.top;
      var idx = 0;
      for (var k = 0; k < centers.length; k++) if (centers[k] <= line + 1) idx = k;
      var span = centers[centers.length - 1] - centers[0];
      steps.style.setProperty("--p", clamp((line - centers[0]) / span, 0, 1).toFixed(4));
      if (idx === current) return;
      current = idx;
      items.forEach(function (li, k) { li.classList.toggle("on", k === idx); });
      shots.forEach(function (im, k) {
        im.classList.toggle("is-on", k === idx);
        im.setAttribute("aria-hidden", k === idx ? "false" : "true");
      });
    };

    scrollJobs.push(update);
    if ("ResizeObserver" in window) new ResizeObserver(measure).observe(steps);
    else window.addEventListener("load", measure);
    measure();
  }

  /* ------------------------------------------------ pricing toggle --- */
  var billing = $(".billing");
  if (billing) {
    billing.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-plan]");
      if (!btn || btn.getAttribute("aria-pressed") === "true") return;
      var plan = btn.dataset.plan;
      billing.dataset.active = plan;
      $$("button", billing).forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      $$(".plans").forEach(function (p) {
        var show = p.id === "plans-" + plan;
        p.hidden = !show;
        if (show && !reduce()) {
          p.classList.remove("entering"); void p.offsetWidth; p.classList.add("entering");
        }
      });
    });
  }

  /* ------------------------------------------------ FAQ -------------- */
  // Smooth open/close for <details>. Without JS (or with reduced motion)
  // they still open and close instantly, as normal.
  $$(".faq-list details").forEach(function (d) {
    var summary = $("summary", d);
    var answer = $("p", d);
    var anim = null, state = "idle";

    function finish() {
      if (state === "closing") d.open = false;
      d.classList.remove("closing");
      d.style.overflow = "";
      anim = null; state = "idle";
    }
    summary.addEventListener("click", function (e) {
      if (reduce() || !d.animate) return;
      e.preventDefault();
      var from = d.offsetHeight;
      if (anim) { anim.cancel(); anim = null; }
      var opening = state === "closing" || !d.open;
      var border = d.offsetHeight - d.clientHeight;
      d.style.overflow = "hidden";
      if (opening) {
        d.classList.remove("closing");
        d.open = true; state = "opening";
        var to = d.offsetHeight;
        if (answer) answer.animate({ opacity: [0, 1], transform: ["translateY(-4px)", "none"] }, { duration: 280, easing: "ease-out" });
        anim = d.animate({ height: [from + "px", to + "px"] }, { duration: 320, easing: "cubic-bezier(.2,.8,.2,1)" });
      } else {
        state = "closing";
        d.classList.add("closing");
        anim = d.animate({ height: [from + "px", (summary.offsetHeight + border) + "px"] }, { duration: 240, easing: "cubic-bezier(.2,.8,.2,1)" });
      }
      anim.onfinish = finish;
    });
  });

  /* ------------------------------------------------ contact form ----- */
  // Set data-endpoint on the form (e.g. a Formspree URL) to post submissions.
  // With no endpoint, the form opens the visitor's email app pre-filled instead.
  var form = $("form[data-contact]");
  if (form) {
    var status = $(".form-status", form);
    var show = function (msg, ok) {
      status.hidden = false;
      status.className = "form-status " + (ok ? "ok" : "err");
      status.textContent = msg;
    };
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if ($('[name="_gotcha"]', form).value) return; // bot trap
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      var endpoint = form.dataset.endpoint;
      if (!endpoint) {
        var body = "Name: " + data.get("name") + "\nEmail: " + data.get("email") +
          "\nPhone: " + (data.get("phone") || "-") + "\nOrganization: " + (data.get("company") || "-") +
          "\n\n" + data.get("message");
        window.location.href = "mailto:" + form.dataset.mailto +
          "?subject=" + encodeURIComponent("Website inquiry from " + data.get("name")) +
          "&body=" + encodeURIComponent(body);
        show("Your email app should open with your message ready to send.", true);
        return;
      }
      var btn = $('button[type="submit"]', form);
      btn.disabled = true;
      fetch(endpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          form.reset();
          show("Message sent. We'll reply within one business day.", true);
        })
        .catch(function () {
          show("The message didn't send. Check your connection and try again, or email " + form.dataset.mailto + ".", false);
        })
        .finally(function () { btn.disabled = false; });
    });
  }

  /* ------------------------------------------------ misc ------------- */
  var y = $("[data-year]");
  if (y) y.textContent = new Date().getFullYear();

  requestTick(); // set the initial scroll-dependent state
})();
