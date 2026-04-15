/**
 * Positions the flying ladybug landing point from an anchor element (hero "P").
 * Sets --lb-land-x / --lb-land-y as percentages of the flight zone.
 * Drives --lb-heading from motion so the bug faces its velocity (hero perch aims at takeoff).
 */
(function () {
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced.matches) return;

  function debounce(fn, ms) {
    var t;
    return function () {
      clearTimeout(t);
      var args = arguments;
      t = setTimeout(function () {
        fn.apply(null, args);
      }, ms);
    };
  }

  function headingFromPctDelta(dLeftPct, dTopPct, zone) {
    var dx = (dLeftPct / 100) * zone.clientWidth;
    var dy = (dTopPct / 100) * zone.clientHeight;
    return (Math.atan2(dx, -dy) * 180) / Math.PI;
  }

  function getKeyframeProgress(mile) {
    if (!mile.getAnimations) return null;
    var list = mile.getAnimations();
    for (var i = 0; i < list.length; i++) {
      var anim = list[i];
      var name = anim.animationName;
      if (!name) continue;
      if (name.indexOf("ladybug-hero-fly") === -1 && name.indexOf("ladybug-ambient-fly") === -1) {
        continue;
      }
      var effect = anim.effect;
      if (!effect || !effect.getTiming) continue;
      var timing = effect.getTiming();
      var dur = timing.duration;
      if (typeof dur !== "number" || !isFinite(dur) || dur <= 0) continue;
      var ct = anim.currentTime;
      if (ct == null || !isFinite(ct)) continue;
      if (ct < 0) ct = 0;
      var t = ((ct % dur) + dur) % dur;
      return { name: name, t: t / dur };
    }
    return null;
  }

  function tickHeading() {
    var miles = document.querySelectorAll(".ladybug-flight__mile");
    for (var i = 0; i < miles.length; i++) {
      var mile = miles[i];
      var zone = mile.closest(".ladybug-flight");
      if (!zone) continue;
      var cs = getComputedStyle(mile);
      var l = parseFloat(cs.left);
      var topPx = parseFloat(cs.top);
      if (isNaN(l) || isNaN(topPx)) continue;

      var prev = mile._lbHeadingPrev;
      var raw = prev ? prev.lastHeading : null;

      var dx = prev && !isNaN(prev.l) ? l - prev.l : 0;
      var dy = prev && !isNaN(prev.t) ? topPx - prev.t : 0;
      if (dx * dx + dy * dy > 0.04) {
        raw = (Math.atan2(dx, -dy) * 180) / Math.PI;
      }

      var ap = getKeyframeProgress(mile);
      var isHero = ap && ap.name.indexOf("ladybug-hero-fly") !== -1;
      if (isHero) {
        /* Takeoff heading on P (~25.6%–30% with arc-length-timed ladybug-hero-fly) */
        if (ap.t >= 0.252 && ap.t < 0.3) {
          raw = headingFromPctDelta(1.2, -3.5, zone);
        } else if (ap.t < 0.04) {
          raw = headingFromPctDelta(4, -0.5, zone);
        }
      }

      if (raw == null || isNaN(raw)) {
        if (zone.classList.contains("ladybug-flight--ambient")) {
          raw = headingFromPctDelta(12, -2, zone);
        } else {
          raw = headingFromPctDelta(4, -0.5, zone);
        }
      }

      var smooth = mile._lbHeadingSmooth;
      if (smooth == null || isNaN(smooth)) {
        smooth = raw;
      } else {
        var delta = raw - smooth;
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        /* Snap on loop glitch; otherwise ease rotation toward velocity */
        if (Math.abs(delta) > 85) {
          smooth = raw;
        } else {
          smooth += delta * 0.2;
        }
      }
      mile._lbHeadingSmooth = smooth;
      mile.style.setProperty("--lb-heading", smooth.toFixed(2) + "deg");
      mile._lbHeadingPrev = { l: l, t: topPx, lastHeading: raw };
    }
    requestAnimationFrame(tickHeading);
  }

  function updateFlight(flight) {
    var sel = flight.getAttribute("data-ladybug-anchor");
    if (!sel) return;
    var anchor = document.querySelector(sel);
    var zone =
      flight.closest(".intro-section--sketch") ||
      flight.closest(".about-section--page") ||
      flight.parentElement;
    if (!anchor || !zone) return;
    var ar = anchor.getBoundingClientRect();
    var zr = zone.getBoundingClientRect();
    if (zr.width <= 0 || zr.height <= 0) return;
    /* Perch on top of the “P” cap (reads like sitting on the letter; z-index keeps bug in front) */
    var px = ((ar.left + ar.width * 0.46 - zr.left) / zr.width) * 100;
    var py = ((ar.top + ar.height * 0.14 - zr.top) / zr.height) * 100;
    px = Math.max(4, Math.min(92, px));
    py = Math.max(6, Math.min(88, py));
    flight.style.setProperty("--lb-land-x", px.toFixed(2) + "%");
    flight.style.setProperty("--lb-land-y", py.toFixed(2) + "%");
  }

  function boot() {
    var flights = document.querySelectorAll(".ladybug-flight[data-ladybug-anchor]");
    if (!flights.length) return;

    function all() {
      for (var i = 0; i < flights.length; i++) updateFlight(flights[i]);
    }

    all();
    requestAnimationFrame(function () {
      requestAnimationFrame(all);
    });
    var onResize = debounce(all, 120);
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onResize, { passive: true });
    window.addEventListener("load", all);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(all).catch(function () {});
    }
  }

  function bootHeading() {
    requestAnimationFrame(tickHeading);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
    document.addEventListener("DOMContentLoaded", bootHeading);
  } else {
    boot();
    bootHeading();
  }
})();
